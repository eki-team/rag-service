"""
Solución definitiva para el problema de DNS/Firewall con MongoDB Atlas
Usa múltiples métodos de resolución DNS que bypasean el firewall
"""
import socket
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


def resolve_mongodb_hosts_bypass_firewall(hosts: List[str]) -> dict:
    """
    Intenta resolver hosts de MongoDB usando métodos alternativos
    que bypasean el firewall que bloquea puerto 53
    
    Args:
        hosts: Lista de hosts a resolver (ej: ["nasakb.yvrx6cs-shard-00-00.mongodb.net"])
    
    Returns:
        Dict con {host: ip} resueltos
    """
    resolved = {}
    
    for host in hosts:
        ip = None
        
        # Método 1: Intentar con socket getaddrinfo (usa cache del sistema)
        try:
            result = socket.getaddrinfo(host, 27017, socket.AF_INET)
            if result:
                ip = result[0][4][0]
                logger.info(f"✅ Resolved {host} → {ip} (via system cache)")
        except Exception as e:
            logger.debug(f"Method 1 failed for {host}: {e}")
        
        # Método 2: DNS over HTTPS (bypasea firewall)
        if not ip:
            try:
                import httpx
                url = f"https://dns.google/resolve?name={host}&type=A"
                response = httpx.get(url, timeout=5)
                data = response.json()
                if 'Answer' in data:
                    for record in data['Answer']:
                        if record.get('type') == 1:  # A record
                            ip = record['data']
                            logger.info(f"✅ Resolved {host} → {ip} (via DNS over HTTPS)")
                            break
            except Exception as e:
                logger.debug(f"Method 2 failed for {host}: {e}")
        
        # Método 3: Cloudflare DNS over HTTPS
        if not ip:
            try:
                import httpx
                url = f"https://cloudflare-dns.com/dns-query?name={host}&type=A"
                headers = {"Accept": "application/dns-json"}
                response = httpx.get(url, headers=headers, timeout=5)
                data = response.json()
                if 'Answer' in data:
                    for record in data['Answer']:
                        if record.get('type') == 1:
                            ip = record['data']
                            logger.info(f"✅ Resolved {host} → {ip} (via Cloudflare DoH)")
                            break
            except Exception as e:
                logger.debug(f"Method 3 failed for {host}: {e}")
        
        if ip:
            resolved[host] = ip
        else:
            logger.warning(f"⚠️ Could not resolve {host} using any method")
    
    return resolved


def patch_hosts_file_windows(host_ip_map: dict) -> bool:
    """
    Añade hosts al archivo hosts de Windows (requiere permisos admin)
    
    Args:
        host_ip_map: Dict con {hostname: ip}
    
    Returns:
        True si se pudo modificar
    """
    import platform
    
    if platform.system() != 'Windows':
        logger.warning("⚠️ Esta función solo funciona en Windows")
        return False
    
    hosts_file = r"C:\Windows\System32\drivers\etc\hosts"
    
    try:
        # Leer archivo actual
        with open(hosts_file, 'r') as f:
            lines = f.readlines()
        
        # Marcar hosts ya existentes
        existing_hosts = set()
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    existing_hosts.add(parts[1])
        
        # Preparar nuevas líneas
        new_lines = []
        for host, ip in host_ip_map.items():
            if host not in existing_hosts:
                new_lines.append(f"{ip}    {host}  # MongoDB Atlas (added by RAG service)\n")
        
        if new_lines:
            # Intentar escribir (requiere admin)
            with open(hosts_file, 'a') as f:
                f.write("\n# MongoDB Atlas hosts (added automatically)\n")
                f.writelines(new_lines)
            
            logger.info(f"✅ Added {len(new_lines)} hosts to {hosts_file}")
            return True
        else:
            logger.info("ℹ️ All hosts already in hosts file")
            return True
            
    except PermissionError:
        logger.error(f"❌ No permission to modify {hosts_file} - need admin rights")
        return False
    except Exception as e:
        logger.error(f"❌ Error modifying hosts file: {e}")
        return False


def suggest_manual_hosts_file_update(host_ip_map: dict) -> str:
    """
    Genera instrucciones para actualizar manualmente el archivo hosts
    
    Returns:
        String con instrucciones
    """
    lines = [
        "\n" + "="*70,
        "SOLUCIÓN: Añadir hosts manualmente al archivo hosts de Windows",
        "="*70,
        "",
        "1. Abre PowerShell COMO ADMINISTRADOR",
        "2. Ejecuta:",
        "   notepad C:\\Windows\\System32\\drivers\\etc\\hosts",
        "",
        "3. Añade estas líneas al FINAL del archivo:",
        "",
        "# MongoDB Atlas - nasakb cluster",
    ]
    
    for host, ip in host_ip_map.items():
        lines.append(f"{ip}    {host}")
    
    lines.extend([
        "",
        "4. Guarda el archivo (Ctrl+S)",
        "5. Ejecuta: ipconfig /flushdns",
        "6. Reinicia tu aplicación",
        "",
        "="*70,
    ])
    
    return "\n".join(lines)


def auto_fix_mongodb_dns():
    """
    Intenta resolver automáticamente el problema de DNS de MongoDB Atlas
    """
    logger.info("🔧 Intentando resolver problema de DNS para MongoDB Atlas...")
    
    # Hosts de MongoDB Atlas que necesitamos resolver
    hosts = [
        "nasakb.yvrx6cs-shard-00-00.mongodb.net",
        "nasakb.yvrx6cs-shard-00-01.mongodb.net",
        "nasakb.yvrx6cs-shard-00-02.mongodb.net",
    ]
    
    # Intentar resolver
    resolved = resolve_mongodb_hosts_bypass_firewall(hosts)
    
    if not resolved:
        logger.error("❌ No se pudo resolver ningún host de MongoDB Atlas")
        logger.info("\n💡 SOLUCIONES POSIBLES:")
        logger.info("1. Desactivar firewall temporalmente")
        logger.info("2. Cambiar DNS del sistema a Google (8.8.8.8)")
        logger.info("3. Usar VPN o hotspot del móvil")
        logger.info("4. Añadir hosts manualmente al archivo hosts")
        return False
    
    logger.info(f"✅ Resueltos {len(resolved)}/{len(hosts)} hosts")
    
    # Intentar parchear archivo hosts
    if patch_hosts_file_windows(resolved):
        logger.info("✅ Hosts añadidos al archivo hosts de Windows")
        logger.info("🔄 Reinicia la aplicación para que tome efecto")
        return True
    else:
        # Si no se pudo parchear, mostrar instrucciones
        instructions = suggest_manual_hosts_file_update(resolved)
        logger.warning(instructions)
        return False


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    auto_fix_mongodb_dns()
