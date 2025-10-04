# Script para obtener las IPs de MongoDB Atlas y configurar el archivo hosts
# Requiere ejecutarse como Administrador

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🔧 MongoDB Atlas - Configurador de Hosts" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Hostnames de MongoDB
$mongoHosts = @(
    "nasakb.yvrx6cs-shard-00-00.mongodb.net",
    "nasakb.yvrx6cs-shard-00-01.mongodb.net",
    "nasakb.yvrx6cs-shard-00-02.mongodb.net"
)

# Intentar resolver con diferentes métodos
Write-Host "📡 Intentando resolver hostnames..." -ForegroundColor Yellow
Write-Host ""

$resolvedIPs = @{}

foreach ($host in $mongoHosts) {
    Write-Host "   🔍 Resolviendo: $host" -ForegroundColor Gray
    
    # Método 1: Usando Resolve-DnsName (puede fallar con firewall)
    try {
        $result = Resolve-DnsName -Name $host -ErrorAction Stop
        if ($result) {
            $ip = $result[0].IPAddress
            if ($ip) {
                $resolvedIPs[$host] = $ip
                Write-Host "      ✅ IP encontrada: $ip" -ForegroundColor Green
                continue
            }
        }
    } catch {
        Write-Host "      ⚠️  Resolve-DnsName falló (firewall bloqueando)" -ForegroundColor DarkYellow
    }
    
    # Método 2: Usando nslookup con DNS público
    try {
        $nslookup = nslookup $host 8.8.8.8 2>&1 | Select-String "Address:" | Select-Object -Last 1
        if ($nslookup) {
            $ip = ($nslookup -replace "Address:\s+", "").Trim()
            if ($ip -match "^\d+\.\d+\.\d+\.\d+$") {
                $resolvedIPs[$host] = $ip
                Write-Host "      ✅ IP encontrada (nslookup): $ip" -ForegroundColor Green
                continue
            }
        }
    } catch {
        Write-Host "      ⚠️  nslookup también falló" -ForegroundColor DarkYellow
    }
    
    # Si llegamos aquí, no pudimos resolver
    Write-Host "      ❌ No se pudo resolver (DNS bloqueado)" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

# Verificar si obtuvimos todas las IPs
if ($resolvedIPs.Count -eq 3) {
    Write-Host "✅ ¡Todas las IPs obtenidas exitosamente!" -ForegroundColor Green
    Write-Host ""
    
    # Mostrar IPs
    Write-Host "📋 IPs a agregar al archivo hosts:" -ForegroundColor Yellow
    foreach ($entry in $resolvedIPs.GetEnumerator()) {
        Write-Host "   $($entry.Value)    $($entry.Key)" -ForegroundColor White
    }
    Write-Host ""
    
    # Preguntar si quiere agregar automáticamente
    $response = Read-Host "¿Deseas agregar estas IPs al archivo hosts automáticamente? (S/N)"
    
    if ($response -eq "S" -or $response -eq "s" -or $response -eq "Y" -or $response -eq "y") {
        # Verificar si se ejecuta como administrador
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if (-not $isAdmin) {
            Write-Host ""
            Write-Host "❌ ERROR: Se requieren permisos de Administrador" -ForegroundColor Red
            Write-Host "💡 Ejecuta este script con 'Ejecutar como Administrador'" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Presiona cualquier tecla para salir..."
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
        
        # Ruta del archivo hosts
        $hostsPath = "C:\Windows\System32\drivers\etc\hosts"
        
        # Leer contenido actual
        $hostsContent = Get-Content $hostsPath
        
        # Verificar si ya existen entradas de MongoDB
        $mongoEntriesExist = $hostsContent | Where-Object { $_ -match "nasakb.yvrx6cs.*mongodb.net" }
        
        if ($mongoEntriesExist) {
            Write-Host ""
            Write-Host "⚠️  Ya existen entradas de MongoDB en el archivo hosts" -ForegroundColor Yellow
            $overwrite = Read-Host "¿Deseas sobrescribirlas? (S/N)"
            
            if ($overwrite -eq "S" -or $overwrite -eq "s" -or $overwrite -eq "Y" -or $overwrite -eq "y") {
                # Eliminar entradas antiguas
                $hostsContent = $hostsContent | Where-Object { $_ -notmatch "nasakb.yvrx6cs.*mongodb.net" }
            } else {
                Write-Host "❌ Operación cancelada" -ForegroundColor Red
                exit 0
            }
        }
        
        # Agregar nuevas entradas
        $newEntries = @()
        $newEntries += ""
        $newEntries += "# MongoDB Atlas - nasakb cluster (agregado automáticamente)"
        foreach ($entry in $resolvedIPs.GetEnumerator()) {
            $newEntries += "$($entry.Value)    $($entry.Key)"
        }
        
        # Escribir al archivo
        try {
            $hostsContent + $newEntries | Set-Content $hostsPath -Force
            Write-Host ""
            Write-Host "✅ ¡Archivo hosts actualizado exitosamente!" -ForegroundColor Green
            Write-Host ""
            
            # Limpiar caché DNS
            Write-Host "🔄 Limpiando caché DNS..." -ForegroundColor Yellow
            ipconfig /flushdns | Out-Null
            Write-Host "✅ Caché DNS limpiada" -ForegroundColor Green
            Write-Host ""
            
            # Verificar
            Write-Host "✅ Verificando configuración..." -ForegroundColor Yellow
            foreach ($host in $mongoHosts) {
                $pingResult = Test-Connection -ComputerName $host -Count 1 -ErrorAction SilentlyContinue
                if ($pingResult) {
                    Write-Host "   ✅ $host -> OK" -ForegroundColor Green
                } else {
                    Write-Host "   ⚠️  $host -> No responde a ping (normal si MongoDB no acepta ping)" -ForegroundColor DarkYellow
                }
            }
            
            Write-Host ""
            Write-Host "============================================" -ForegroundColor Cyan
            Write-Host "✅ ¡CONFIGURACIÓN COMPLETA!" -ForegroundColor Green
            Write-Host "============================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Ahora puedes probar la conexión con:" -ForegroundColor White
            Write-Host "   python test_mongo_simple.py" -ForegroundColor Cyan
            Write-Host ""
            
        } catch {
            Write-Host ""
            Write-Host "❌ ERROR al escribir el archivo hosts: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host ""
        }
    } else {
        Write-Host ""
        Write-Host "📋 Copia estas líneas manualmente al archivo hosts:" -ForegroundColor Yellow
        Write-Host "   C:\Windows\System32\drivers\etc\hosts" -ForegroundColor Gray
        Write-Host ""
        Write-Host "# MongoDB Atlas - nasakb cluster" -ForegroundColor White
        foreach ($entry in $resolvedIPs.GetEnumerator()) {
            Write-Host "$($entry.Value)    $($entry.Key)" -ForegroundColor White
        }
        Write-Host ""
    }
    
} else {
    Write-Host "❌ No se pudieron resolver todas las IPs" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔥 Tu firewall está bloqueando DNS completamente" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 SOLUCIONES ALTERNATIVAS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1️⃣  Conecta tu PC a un hotspot móvil (celular)" -ForegroundColor White
    Write-Host "   - Desactiva WiFi" -ForegroundColor Gray
    Write-Host "   - Activa hotspot en tu celular" -ForegroundColor Gray
    Write-Host "   - Conéctate y ejecuta este script nuevamente" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2️⃣  Usa una VPN (ProtonVPN, Windscribe gratis)" -ForegroundColor White
    Write-Host "   - Descarga e instala una VPN" -ForegroundColor Gray
    Write-Host "   - Conéctate y ejecuta este script nuevamente" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3️⃣  Desactiva temporalmente el firewall/antivirus" -ForegroundColor White
    Write-Host "   - Windows Defender -> Desactivar protección en tiempo real" -ForegroundColor Gray
    Write-Host "   - Ejecuta este script nuevamente" -ForegroundColor Gray
    Write-Host "   - Reactiva la protección después" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4️⃣  Usa MongoDB Compass para obtener las IPs:" -ForegroundColor White
    Write-Host "   - Abre MongoDB Compass (funciona)" -ForegroundColor Gray
    Write-Host "   - Conéctate a nasakb" -ForegroundColor Gray
    Write-Host "   - Ve a Performance/Server Status" -ForegroundColor Gray
    Write-Host "   - Copia las IPs manualmente" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Presiona cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
