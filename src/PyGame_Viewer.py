import numpy as np
import pygame
from PIL import Image, ImageOps, ImageDraw
import roar_py_interface
from typing import Optional, Dict, Any

class PyGameViewer:
    def __init__(
        self
    ):
        self.screen = None
        self.clock = None
        
    
    def init_pygame(self, x, y) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((x, y), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("RoarPy Viewer")
        pygame.key.set_repeat()
        self.clock = pygame.time.Clock()

    def render(self, image : roar_py_interface.RoarPyCameraSensorData, image2 : roar_py_interface.RoarPyCameraSensorDataDepth) -> Optional[Dict[str, Any]]:
        image_pil = image.get_image()
        image2_np = image2.image_depth
        image2_np = image2_np[100:150, len(image2_np) - 50: len(image2_np) + 50]
        #image2_np = np.log(image2_np)
        image2_np = np.clip(image2_np , 0, 40)

        min, max = np.min(image2_np), np.max(image2_np)
        min, max = 0, 40
        normalized_image = (image2_np) / (max-min)
        normalized_image = (normalized_image * 255).astype(np.uint8)
        image2_pil = Image.fromarray(normalized_image,mode="L")
        #image2_pil = ImageOps.invert(image2_pil)
        if self.screen is None:
            self.init_pygame(image_pil.width + image2_pil.width, image_pil.height)
        
        depth_value = np.average(image2_np)
        depth_value_text = ImageDraw.Draw(image2_pil)
        depth_value_text.text((2,2), str(depth_value), fill= 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
        
        combined_img_pil = Image.new('RGB',(image_pil.width + image2_pil.width, image_pil.height), (250,250,250))
        combined_img_pil.paste(image_pil, (0,0))
        combined_img_pil.paste(image2_pil, (image_pil.width,0))
        image_surface = pygame.image.fromstring(combined_img_pil.tobytes(), combined_img_pil.size, combined_img_pil.mode).convert()
        self.screen.fill((0,0,0))
        self.screen.blit(image_surface, (0, 0))
       
        pygame.display.flip()
        self.clock.tick(60)
        return depth_value
    