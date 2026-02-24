# Bespoke Stack Integration Plan
## Private AI & Home Integration for Juma Family

**Created:** February 24, 2026  
**Status:** Research Complete - Ready for Implementation  
**Target Environment:** Gibson's Server (10.144.118.159)

---

## 1. Executive Summary

The **Bespoke Stack** is a modular, containerized system that brings together:
- **Ollama** — Local AI backbone (Llama, Mistral, etc.)
- **Open WebUI** — Chat interface for AI interactions
- **Home Assistant** — Smart home bridge (lights, thermostats, security)
- **Custom Apps** — Concierge & Wellness microservices

**Current State:** No Bespoke Stack services are currently deployed. Gibson's server runs a microservices stack (Kong, Keycloak, services A-C) but lacks the AI + home integration layer.

---

## 2. Gap Analysis

| Requirement | Current State | Action Needed |
|-------------|---------------|---------------|
| Ollama (AI) | ❌ Not installed | Deploy container |
| Open WebUI | ❌ Not installed | Deploy container |
| Home Assistant | ❌ Not installed | Deploy container |
| GPU Acceleration | Unknown | Check NVIDIA drivers |
| Smart Home Devices | Not integrated | Inventory devices |
| Concierge App | ❌ Not built | Create FastAPI service |
| Wellness App | ❌ Not built | Create FastAPI service |

---

## 3. Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Verify NVIDIA GPU + Container Toolkit on Gibson's server
- [ ] Create `bespoke_stack` directory structure
- [ ] Write `compose.yml` with all 5 services
- [ ] Configure Docker network and volumes

### Phase 2: Core Services (Week 2)
- [ ] Deploy Ollama + pull base models (llama3, mistral)
- [ ] Deploy Open WebUI and verify AI connectivity
- [ ] Deploy Home Assistant
- [ ] Access HA dashboard at http://server:8123

### Phase 3: Home Integration (Week 3)
- [ ] Discover IoT devices on home network
- [ ] Add Zigbee/Z-Wave hubs to HA
- [ ] Create HA automations (mood lighting, climate)
- [ ] Test AI → HA API calls

### Phase 4: Custom Apps (Week 4)
- [ ] Build Concierge App (FastAPI + Ollama + HA)
- [ ] Build Wellness App (FastAPI + Ollama + HA + Wearables)
- [ ] Implement RAG for personal data (calendar, preferences)
- [ ] Voice integration (Wyoming/Speech to Text)

---

## 4. Docker Compose Blueprint

```yaml
version: '3.9'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: bespoke_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: bespoke_webui
    ports:
      - "8080:8080"
    volumes:
      - open_webui_data:/app/backend/data
    environment:
      - OLLAMA_API_BASE=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

  home-assistant:
    image: homeassistant/home-assistant:latest
    container_name: bespoke_ha
    ports:
      - "8123:8123"
    volumes:
      - ha_config:/config
      - /etc/localtime:/etc/localtime:ro
    environment:
      - TZ=Africa/Nairobi
    privileged: true
    restart: unless-stopped

  concierge-app:
    build: ./concierge
    container_name: bespoke_concierge
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - HA_HOST=http://home-assistant:8123
    depends_on:
      - ollama
      - home-assistant
    restart: unless-stopped

  wellness-app:
    build: ./wellness
    container_name: bespoke_wellness
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - HA_HOST=http://home-assistant:8123
    depends_on:
      - ollama
      - home-assistant
    restart: unless-stopped

volumes:
  ollama_data:
  open_webui_data:
  ha_config:
```

---

## 5. Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16GB | 32GB+ |
| GPU | None | NVIDIA RTX 3060+ |
| Storage | 100GB SSD | 500GB NVMe |
| Network | 100Mbps | 1Gbps |

**Check command:**
```bash
ssh gibz@10.144.118.159 "nvidia-smi"
```

---

## 6. Smart Home Device Strategy

### Current Assumptions (Need Verification)
- Philips Hue lights
- Thermostat (Nest/Ecobee)
- Security cameras
- Zigbee/Z-Wave hub

### Integration Points
1. **HA Discovery** — Auto-scan network for devices
2. **MQTT Bridge** — For custom IoT sensors
3. **REST API** — Custom apps → HA for actions

---

## 7. Custom App Specifications

### Concierge App
```python
# /concierge/main.py
from fastapi import FastAPI
import ollama

app = FastAPI()

@app.get("/book")
def book_experience(experience: str, location: str):
    # Use Ollama to find best options
    response = ollama.chat(model='llama3', messages=[
        {"role": "user", "content": f"Find best {experience} in {location}"}
    ])
    # Call HA to adjust ambiance
    return {"status": "booked", "details": response}
```

### Wellness App
```python
# /wellness/main.py
from fastapi import FastAPI
import ollama

app = FastAPI()

@app.get("/advice")
def get_wellness_advice():
    # Pull wearable data via HA API
    # Process with Ollama
    return {"recommendation": "30min meditation", "mood": "stressed"}
```

---

## 8. Security Considerations

- [ ] Long-lived HA access tokens for API calls
- [ ] Nginx reverse proxy with auth
- [ ] Network segmentation (IoT VLAN)
- [ ] TLS for all external ports
- [ ] Fail2ban on SSH

---

## 9. Next Steps (Immediate Actions)

1. **GPU Verification** — Check if Gibson's server has NVIDIA GPU
2. **Directory Creation** — Create `bespoke_stack/` on Gibson's server
3. **Initial Deploy** — Start with Ollama + Open WebUI only
4. **Model Pull** — `docker exec bespoke_ollama ollama pull llama3`

---

## 10. References

- Ollama: https://ollama.ai
- Open WebUI: https://github.com/open-webui/open-webui
- Home Assistant: https://www.home-assistant.io
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/

---

**Plan Author:** Ahie Juma (Agentic Support)  
**For:** Gibson Juma - Sovereign Infrastructure Expansion
