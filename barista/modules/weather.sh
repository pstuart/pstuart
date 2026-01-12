# =============================================================================
# Weather Module - Shows current weather (uses wttr.in)
# =============================================================================

_weather_get_file_mtime() {
    local file="$1"
    if [ "$(uname)" = "Darwin" ]; then
        stat -f %m "$file" 2>/dev/null || echo 0
    else
        stat -c %Y "$file" 2>/dev/null || echo 0
    fi
}

module_weather() {
    local location="${WEATHER_LOCATION:-}"
    local units="${WEATHER_UNITS:-m}"
    local cache_ttl="${WEATHER_CACHE_TTL:-1800}"
    local cache_file="/tmp/.claude_weather_cache"
    local weather_data=""

    # Check cache
    if [ -f "$cache_file" ]; then
        local cache_age=$(($(date +%s) - $(_weather_get_file_mtime "$cache_file")))
        if [ "$cache_age" -lt "$cache_ttl" ]; then
            weather_data=$(cat "$cache_file")
        fi
    fi

    # Fetch fresh data if needed
    if [ -z "$weather_data" ]; then
        local url="https://wttr.in/${location}?format=%c|%t&${units}"
        weather_data=$(curl -s --max-time 3 "$url" 2>/dev/null)
        # Check for valid response
        if [ -n "$weather_data" ]; then
            case "$weather_data" in
                *Unknown*|*Sorry*|*Error*) weather_data="" ;;
                *) echo "$weather_data" > "$cache_file" 2>/dev/null ;;
            esac
        fi
    fi

    if [ -z "$weather_data" ]; then
        return
    fi

    # Parse: format is "icon|temp" like "⛅️|-7°C"
    local cond_icon=""
    local temp=""
    
    case "$weather_data" in
        *"|"*)
            cond_icon=$(echo "$weather_data" | cut -d"|" -f1 | tr -d " ")
            temp=$(echo "$weather_data" | cut -d"|" -f2 | tr -d " ")
            ;;
        *)
            # Fallback
            temp=$(echo "$weather_data" | grep -oE "[-+]?[0-9]+°[CF]" | tail -1)
            cond_icon=$(echo "$weather_data" | sed "s/$temp//" | tr -d " ")
            ;;
    esac

    echo "${cond_icon}${temp}"
}
