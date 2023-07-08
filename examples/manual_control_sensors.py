from roar_py_carla import roar_py_carla
import roar_py_interface
import carla
import pygame
from PIL import Image
import numpy as np
import asyncio
from typing import Optional, Dict, Any

class ManualControlViewer:
    def __init__(
        self
    ):
        self.screen = None
        self.clock = None
        self.last_control = {
            "throttle": 0.0,
            "steer": 0.0,
            "brake": 0.0,
            "hand_brake": np.array([0]),
            "reverse": np.array([0])
        }
    
    def init_pygame(self, x, y) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((x, y), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("RoarPy Manual Control Viewer")
        pygame.key.set_repeat()
        self.clock = pygame.time.Clock()

    def render(self, image : roar_py_interface.RoarPyCameraSensorData) -> Optional[Dict[str, Any]]:
        image_pil : Image = image.get_image()
        if self.screen is None:
            self.init_pygame(image_pil.width, image_pil.height)
        if image_pil.mode != 'RGB':
            image_pil = image_pil.convert('RGB')
        new_control = {
            "throttle": 0.0,
            "steer": 0.0,
            "brake": 0.0,
            "hand_brake": np.array([0]),
            "reverse": np.array([0])
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
        
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
            new_control['throttle'] = 0.2
        if pressed_keys[pygame.K_DOWN] or pressed_keys[pygame.K_s]:
            new_control['brake'] = 0.2
        if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
            new_control['steer'] = -0.2
        if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
            new_control['steer'] = 0.2
        
        image_surface = pygame.image.fromstring(image_pil.tobytes(), image_pil.size, image_pil.mode).convert()
        self.screen.fill((0,0,0))
        self.screen.blit(image_surface, (0, 0))
        pygame.display.flip()
        self.clock.tick(60)
        self.last_control = new_control
        return new_control


async def main():
    carla_client = carla.Client('localhost', 2000)
    carla_client.set_timeout(5.0)
    roar_py_instance = roar_py_carla.RoarPyCarlaInstance(carla_client)
    
    carla_world = roar_py_instance.world
    carla_world.set_control_steps(0.05, 0.005)
    carla_world.set_asynchronous(True)
    
    spawn_point, spawn_rpy = carla_world.spawn_points[
        np.random.randint(len(carla_world.spawn_points))
    ]

    way_points = carla_world.maneuverable_waypoints

    vehicle = carla_world.spawn_vehicle(
        "vehicle.tesla.model3",
        way_points[10].location + np.array([0,0,1]),
        way_points[10].roll_pitch_yaw
    )

    camera = vehicle.attach_camera_sensor(
        roar_py_interface.RoarPyCameraSensorDataRGB, # Specify what kind of data you want to receive
        np.array([4.0, 0.0, 1]), # relative position
        np.array([0, 0, 0]), # relative rotation
    )
    depth_camera = vehicle.attach_camera_sensor(
        roar_py_interface.RoarPyCameraSensorDataDepth,
        np.array([4.0, 0.0, 1]), # relative position
        np.array([0, 0, 0]), # relative rotation
    )
    accelerometer = vehicle.attach_accelerometer_sensor(
        roar_py_interface.RoarPyAccelerometerSensorData
    )
    collision_sensor = vehicle.attach_collision_sensor(
        np.array([0.0, 0.0, 1]), 
        np.array([0, 0, 0])
    )
    
    gnss_sensor = vehicle.attach_gnss_sensor()
    
    viewer = ManualControlViewer()

    try:
        while True:
            await carla_world.step()
            img : roar_py_interface.RoarPyCameraSensorDataRGB = await camera.receive_observation()
            depth_img :roar_py_interface.RoarPyCameraSensorDataDepth = await depth_camera.receive_observation()
            accel : roar_py_interface.RoarPyAccelerometerSensorData = await accelerometer.receive_observation()
            collision: roar_py_interface.RoarPyCollisionSensorData = await collision_sensor.receive_observation()
            gnss_data: roar_py_interface.RoarPyGNSSSensorData = await gnss_sensor.receive_observation()

            print(gnss_data)
            print("hello")
            #depth_img.get_image().convert('F').save("depth_img.tiff")
            
            #print(img)
            control = viewer.render(depth_img)
            if control is None:
                break
            await vehicle.apply_action(control)
    finally:
        roar_py_instance.close()

if __name__ == '__main__':
    asyncio.run(main())