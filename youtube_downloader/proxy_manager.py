"""
Proxy Manager for YouTube Downloader

Handles proxy rotation, health checking, failover, and authentication.
Supports HTTP, HTTPS, SOCKS4, and SOCKS5 proxies.
"""

import time
import random
import logging
import threading
from typing import Optional, List, Dict
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for a single proxy."""
    host: str
    port: int
    scheme: str = 'http'  # http, https, socks4, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    last_used: float = 0.0
    failure_count: int = 0
    is_healthy: bool = True
    
    def __repr__(self):
        auth = f"{self.username}:***@" if self.username else ""
        return f"{self.scheme}://{auth}{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to proxy dict for requests library."""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"
        elif self.username:
            auth_part = f"{self.username}@"
        else:
            auth_part = ""
        url = f"{self.scheme}://{auth_part}{self.host}:{self.port}"
        return {
            'http': url,
            'https': url
        }


class ProxyManager:
    """
    Manages proxies with rotation, health checking, and failover.
    
    Features:
    - Automatic rotation
    - Health checking
    - Failure tracking and backoff
    - Support for all proxy types (HTTP, HTTPS, SOCKS4, SOCKS5)
    - Authenticated proxies
    """
    
    def __init__(
        self,
        proxies: Optional[List[ProxyConfig]] = None,
        rotation_interval: int = 10,
        max_failures: int = 3,
        health_check_url: str = "https://www.google.com",
        health_check_timeout: int = 5,
        enable_health_check: bool = True
    ):
        """
        Initialize ProxyManager.
        
        Args:
            proxies: List of proxy configurations
            rotation_interval: Seconds before rotating to next proxy
            max_failures: Max failures before marking proxy as unhealthy
            health_check_url: URL to test proxy health
            health_check_timeout: Timeout for health checks
            enable_health_check: Whether to perform health checks
        """
        self.proxies: List[ProxyConfig] = proxies or []
        self.rotation_interval = rotation_interval
        self.max_failures = max_failures
        self.health_check_url = health_check_url
        self.health_check_timeout = health_check_timeout
        self.enable_health_check = enable_health_check
        
        self.current_proxy_index = 0
        self.start_time = time.time()
        self._lock = threading.RLock()  # Thread safety lock
        
        if self.enable_health_check and self.proxies:
            self._health_check_all()
    
    @classmethod
    def from_file(cls, filepath: str, **kwargs) -> 'ProxyManager':
        """
        Load proxies from a file.
        
        File format (one per line):
        http://host:port
        socks5://user:pass@host:port
        https://host:port
        socks4://host:port
        
        Args:
            filepath: Path to proxy file
            **kwargs: Additional ProxyManager arguments
            
        Returns:
            ProxyManager instance
        """
        proxies = []
        
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    config = cls._parse_proxy_line(line)
                    if config:
                        proxies.append(config)
        except FileNotFoundError:
            raise FileNotFoundError(f"Proxy file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Error reading proxy file: {e}")
        
        return cls(proxies=proxies, **kwargs)
    
    @staticmethod
    def _parse_proxy_line(line: str) -> Optional[ProxyConfig]:
        """
        Parse a proxy line into ProxyConfig.
        
        Examples:
            http://127.0.0.1:8080
            socks5://user:pass@host:port
            https://proxy.example.com:3128
        """
        line = line.strip()
        if not line:
            return None
        
        # Parse scheme and credentials
        if '@' in line:
            auth_part, url_part = line.rsplit('@', 1)
            if '://' in auth_part:
                scheme, auth_info = auth_part.split('://', 1)
            else:
                scheme = 'http'
                auth_info = auth_part
                if '://' in url_part:
                    scheme = url_part.split('://')[0]
                    url_part = url_part.split('://', 1)[1]
            username, password = auth_info.split(':') if ':' in auth_info else (auth_info, None)
        else:
            username, password = None, None
            if '://' in line:
                scheme = line.split('://')[0]
                url_part = line.split('://', 1)[1]
            else:
                scheme = 'http'
                url_part = line
        
        # Parse host and port
        if '/' in url_part:
            url_part = url_part.split('/')[0]
        
        if ':' in url_part:
            host, port_str = url_part.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                return None
        else:
            host = url_part
            if scheme == 'http':
                port = 80
            elif scheme == 'https':
                port = 443
            elif scheme in ('socks4', 'socks5'):
                port = 1080
            else:
                port = 80
        
        return ProxyConfig(
            scheme=scheme.lower(),
            host=host,
            port=port,
            username=username if username else None,
            password=password if password else None
        )
    
    def get_proxy(self) -> Optional[ProxyConfig]:
        """
        Get the next available proxy, rotating if needed.
        
        Returns:
            ProxyConfig or None if no healthy proxies available
        """
        with self._lock:
            if not self.proxies:
                return None
            
            # Get healthy proxies
            healthy_proxies = [p for p in self.proxies if p.is_healthy]
            if not healthy_proxies:
                # Reset all proxies and try again
                for proxy in self.proxies:
                    proxy.is_healthy = True
                    proxy.failure_count = 0
                healthy_proxies = self.proxies
            
            if not healthy_proxies:
                return None
            
            # Check if we need to rotate (time-based or round-robin)
            current_time = time.time()
            time_since_start = current_time - self.start_time
            
            if time_since_start >= self.rotation_interval:
                self.current_proxy_index = (self.current_proxy_index + 1) % len(healthy_proxies)
                self.start_time = current_time
            
            # Get the selected proxy
            selected = healthy_proxies[self.current_proxy_index % len(healthy_proxies)]
            selected.last_used = current_time
            
            return selected
    
    def get_random_proxy(self) -> Optional[ProxyConfig]:
        """Get a random healthy proxy."""
        healthy_proxies = [p for p in self.proxies if p.is_healthy]
        if not healthy_proxies:
            # Reset all proxies
            for proxy in self.proxies:
                proxy.is_healthy = True
                proxy.failure_count = 0
            healthy_proxies = self.proxies
        
        if not healthy_proxies:
            return None
        
        selected = random.choice(healthy_proxies)
        selected.last_used = time.time()
        return selected
    
    def record_success(self, proxy: ProxyConfig):
        """Record a successful request using this proxy."""
        with self._lock:
            proxy.failure_count = 0
            proxy.is_healthy = True
    
    def record_failure(self, proxy: ProxyConfig, error: Optional[Exception] = None):
        """
        Record a failed request and check if proxy should be marked unhealthy.
        
        Args:
            proxy: The proxy that failed
            error: The exception that occurred
        """
        with self._lock:
            proxy.failure_count += 1
            
            if proxy.failure_count >= self.max_failures:
                proxy.is_healthy = False
                if hasattr(error, 'response') and error.response is not None:
                    status_code = error.response.status_code
                    if status_code == 429:
                        logger.warning(f"Proxy {proxy.host}:{proxy.port} rate limited (429)")
                    else:
                        logger.warning(f"Proxy {proxy.host}:{proxy.port} marked unhealthy after {proxy.failure_count} failures")
                else:
                    logger.warning(f"Proxy {proxy.host}:{proxy.port} marked unhealthy after {proxy.failure_count} failures")
    
    def _health_check(self, proxy: ProxyConfig) -> bool:
        """
        Check if a proxy is healthy by making a test request.
        
        Args:
            proxy: Proxy to check
            
        Returns:
            True if proxy is healthy, False otherwise
        """
        try:
            proxies = proxy.to_dict()
            
            # Handle SOCKS proxies
            if proxy.scheme in ('socks4', 'socks5'):
                from urllib.parse import urlparse
                
                socks_version = 'socks4' if proxy.scheme == 'socks4' else 'socks5'
                auth_part = f'{proxy.username}:{proxy.password}@' if proxy.username and proxy.password else (f'{proxy.username}@' if proxy.username else '')
                proxies = {
                    'http': f'{socks_version}://{auth_part}{proxy.host}:{proxy.port}',
                    'https': f'{socks_version}://{auth_part}{proxy.host}:{proxy.port}'
                }
            
            response = requests.get(
                self.health_check_url,
                proxies=proxies,
                timeout=self.health_check_timeout
            )
            
            proxy.is_healthy = response.status_code == 200
            return proxy.is_healthy
            
        except Exception as e:
            proxy.is_healthy = False
            return False
    
    def _health_check_all(self):
        """Check health of all proxies."""
        if not self.enable_health_check:
            return
        
        logger.info("Checking proxy health...")
        for proxy in self.proxies:
            is_healthy = self._health_check(proxy)
            status = "✓" if is_healthy else "✗"
            logger.info(f"{status} {proxy}")
    
    def add_proxy(self, config: ProxyConfig):
        """Add a new proxy to the pool."""
        with self._lock:
            self.proxies.append(config)
        if self.enable_health_check:
            self._health_check(config)
    
    def get_stats(self) -> Dict:
        """Get statistics about the proxy pool."""
        with self._lock:
            total = len(self.proxies)
            healthy = sum(1 for p in self.proxies if p.is_healthy)
            
            return {
                'total': total,
                'healthy': healthy,
                'unhealthy': total - healthy,
                'healthy_ratio': healthy / total if total > 0 else 0
            }

