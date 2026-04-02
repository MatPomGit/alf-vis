# TODO – demo_yolo_utils

## Brakujące funkcjonalności

- [ ] Brak akceleracji GPU — implementacja czysto NumPy (brak CuPy / Triton)
- [ ] Brak obsługi letterbox paddingu (wymaganego przez YOLO v8 pipeline)
- [ ] Brak normalizacji pikseli do `[0.0, 1.0]` jako odrębnej funkcji
- [ ] Brak konwersji BGR → RGB (OpenCV odczytuje w BGR, YOLO oczekuje RGB)
- [ ] Brak pełnego preprocesingu NCHW: resize + pad + normalize jako jeden pipeline
- [ ] Brak benchmarku porównującego czas z `cv2.resize` i `torch.nn.functional.interpolate`
- [ ] Brak testów jednostkowych dla granicznych przypadków (1×1, batch > 1)
- [ ] Brak przykładu end-to-end z ONNX Runtime
