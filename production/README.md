# 🚀 Produção - Real-Time Trading

Este diretório contém código pronto para produção e integração com sistemas reais.

## 📋 Estrutura

```
production/
├── websocket/        ← WebSocket server para MT5 em tempo real
├── servers/          ← HTTP/gRPC servers para integração
└── README.md         ← Este arquivo
```

## 🔌 WebSocket (Quando for para produção)

O servidor WebSocket será implementado aqui para:
- **Receber candles em tempo real** do MT5
- **Enviar predições** para MT5 em millisegundos
- **Manter conexão persistente** com o terminal
- **Log de todas as operações** para auditoria

### Arquitetura Esperada

```python
# production/websocket/server.py (a implementar)

async def start_websocket_server():
    # 1. Carregar modelos treinados do ./models/
    # 2. Iniciar WebSocket em ws://localhost:5000
    # 3. Aguardar candles do MT5
    # 4. Fazer predição em tempo real
    # 5. Enviar resultado de volta para MT5

# production/websocket/client.mq5 (MT5 EA)
# Conectar-se ao WebSocket
# Enviar OHLC do candle mais recente
# Receber predição + confidence
# Executar trade se confidence >= threshold
```

## 🖥️ Servidores HTTP/gRPC (Futura expansão)

Para integração com outros sistemas:
- API HTTP para predições sob demanda
- gRPC para latência ultra-baixa
- Load balancing para múltiplas instâncias
- Métricas Prometheus para monitoramento

## 📊 Modelos Carregados

Todos os modelos estão treinados em `../models/`:
- `ml_ensemble_eurusd.pkl` - Ensemble final (XGB + RF)
- `ml_ensemble_gbpusd.pkl` - Ensemble final (XGB + RF)
- `ml_scaler_eurusd.pkl` - Normalizador de features
- `ml_scaler_gbpusd.pkl` - Normalizador de features

## ⚠️ Status Atual

- ✅ Modelos: Treinados e validados
- ✅ Indicadores: 24 calculados corretamente
- ✅ Backtest: Validado (51-52% win rate)
- ⏳ WebSocket: A implementar quando necessário
- ⏳ Servidores: Roadmap futuro

## 🔐 Configurações de Produção

Criar arquivo `production/config.json` com:

```json
{
  "websocket": {
    "host": "0.0.0.0",
    "port": 5000,
    "max_clients": 10,
    "timeout": 30
  },
  "models": {
    "path": "../models/",
    "auto_reload": false
  },
  "trading": {
    "min_confidence": 0.55,
    "max_positions": 1,
    "position_size": 0.5
  },
  "logging": {
    "level": "INFO",
    "file": "production.log"
  }
}
```

## 🚀 Deploy Checklist

- [ ] Verificar modelos em `../models/`
- [ ] Copiar indicadores de `../src/indicators.py`
- [ ] Implementar WebSocket server
- [ ] Testar com dados históricos simulados
- [ ] Testar com MT5 em demo account
- [ ] Monitorar performance por 1 semana
- [ ] Deploy em conta real com posição pequena
- [ ] Escalar posição conforme confiança

## 📞 Suporte

Referências:
- Documentação ML: `../docs/`
- Código-fonte: `../src/`
- Backtests: `../results/`
- Scripts MT5: `../mql5/`
