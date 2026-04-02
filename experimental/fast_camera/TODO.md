# TODO – fast_camera

## Brakujące funkcjonalności

- [ ] Brak trybu `half=True` (FP16) dla GPU (dodanie zmniejsza zużycie pamięci i zwiększa prędkość)
- [ ] Brak wsparcia dla modeli TensorRT / ONNX Runtime (dalej szybszych niż PyTorch)
- [ ] Brak adaptacyjnego dostosowania `imgsz` do bieżącego FPS (auto-quality)
- [ ] Licznik FPS aktualizowany jest tylko raz na sekundę — brak wygładzania (moving average)
- [ ] Brak opcji zapisu wideo z adnotacjami (`--save-video`)
- [ ] Brak obsługi wielu źródeł kamer jednocześnie (multi-camera)
- [ ] Brak profilu wydajności (`--profile`) z metrykami: opóźnienie klatki, kolejkowanie
- [ ] Brak testów jednostkowych dla `capture_loop` i `inference_loop`
- [ ] Wątek kamery nie obsługuje błędów i/o — niezauważone rozłączenie kamery
