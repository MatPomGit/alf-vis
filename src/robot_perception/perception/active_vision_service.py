from __future__ import annotations
from dataclasses import dataclass
import cv2
import numpy as np
from common.models import ROI
from perception.console import info, warn
@dataclass
class ActiveVisionResult:
    roi: ROI
    mode_name: str
class ActiveVisionService:
    MODE_NAMES = {0: 'DISABLED', 1: 'ACTIVE_VISION_BASELINE', 2: 'FOVEATED_DIFFUSION', 3: 'FOVEATER', 4: 'RETINAVIT'}
    def _full_frame_roi(self, frame_bgr: np.ndarray) -> ROI:
        h,w = frame_bgr.shape[:2]; return ROI(x=0,y=0,width=w,height=h)
    def _baseline_saliency_roi(self, frame_bgr: np.ndarray) -> ROI:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY); saliency = cv2.GaussianBlur(gray, (21,21), 0); _,_,_,max_loc = cv2.minMaxLoc(saliency)
        h,w = gray.shape; roi_w=max(64,w//2); roi_h=max(64,h//2); x=max(0,min(max_loc[0]-roi_w//2,w-roi_w)); y=max(0,min(max_loc[1]-roi_h//2,h-roi_h)); return ROI(x=x,y=y,width=roi_w,height=roi_h)
    def _foveated_diffusion_roi(self, frame_bgr: np.ndarray) -> ROI:
        warn('Wybrano Foveated Diffusion, ale integracja jest szkieletem.'); return self._baseline_saliency_roi(frame_bgr)
    def _foveater_roi(self, frame_bgr: np.ndarray) -> ROI:
        warn('Wybrano FoveaTer, ale integracja jest szkieletem.'); return self._baseline_saliency_roi(frame_bgr)
    def _retinavit_roi(self, frame_bgr: np.ndarray) -> ROI:
        warn('Wybrano RetinaViT, ale integracja jest szkieletem.'); return self._baseline_saliency_roi(frame_bgr)
    def select_roi(self, frame_bgr: np.ndarray, mode: int = 1) -> ActiveVisionResult:
        mode_name = self.MODE_NAMES.get(mode, 'UNKNOWN'); info(f"Uruchamianie wyboru ROI. Tryb: {mode} ({mode_name})")
        if mode == 0: roi = self._full_frame_roi(frame_bgr)
        elif mode == 1: roi = self._baseline_saliency_roi(frame_bgr)
        elif mode == 2: roi = self._foveated_diffusion_roi(frame_bgr)
        elif mode == 3: roi = self._foveater_roi(frame_bgr)
        elif mode == 4: roi = self._retinavit_roi(frame_bgr)
        else: warn(f'Nieznany tryb active vision: {mode}.'); roi = self._full_frame_roi(frame_bgr); mode_name='DISABLED_UNKNOWN_MODE'
        return ActiveVisionResult(roi=roi, mode_name=mode_name)
