from compas_viewer import Viewer
from compas_viewer.events import KeyEvent
from compas.geometry import Sphere, Point, Frame
from PySide6.QtWidgets import QSlider, QLabel, QVBoxLayout, QWidget, QDockWidget
from PySide6.QtCore import Qt
import random

viewer = Viewer()

# Add initial sphere - Sphere takes (radius, frame)
initial_frame = Frame(Point(0, 0, 0))
initial_sphere = Sphere(radius=0.5, frame=initial_frame)
viewer.scene.add(initial_sphere, name="Initial Sphere")

# Variable to store slider value
slider_value = 1.0

def add_sphere():
    """Add a sphere with radius controlled by slider."""
    x = random.uniform(-5, 5)
    y = random.uniform(-5, 5)
    z = random.uniform(-5, 5)
    
    # Use slider_value for the sphere radius
    frame = Frame(Point(x, y, z))
    sphere = Sphere(radius=slider_value, frame=frame)
    obj = viewer.scene.add(sphere, name=f"Sphere_{slider_value:.2f}")

    
    # Initialize the object and add it to buffer manager
    obj.init()
    viewer.renderer.buffer_manager.add_object(obj)
    viewer.renderer.buffer_manager.create_buffers()
    
    # Force a repaint of the viewport
    viewer.renderer.update()
    print(f"Added sphere at ({x:.2f}, {y:.2f}, {z:.2f}) with radius {slider_value:.2f}")

def remove_last_sphere():
    """Remove the last added sphere."""
    if len(viewer.scene.objects) > 1:  # Keep the initial sphere
        obj = viewer.scene.objects[-1]
        print(f"Removing sphere: {obj.name}")
        viewer.scene.remove(obj)
        
        # Clear and rebuild the buffer manager
        viewer.renderer.buffer_manager.clear()
        viewer.renderer.buffer_manager.objects.clear()  # Important: clear the objects dict too
        print("Cleared buffer manager")
        
        for scene_obj in viewer.scene.objects:
            viewer.renderer.buffer_manager.add_object(scene_obj)
            print(f"Re-added {scene_obj.name} to buffer manager")
        
        viewer.renderer.buffer_manager.create_buffers()
        print(f"Recreated buffers. Remaining objects: {len(viewer.scene.objects)}")
        
        viewer.renderer.update()
    else:
        print("Only initial sphere left, cannot remove.")

def on_slider_change(value):
    """Callback when slider value changes."""
    global slider_value
    slider_value = value / 10.0  # Scale to 0.1 - 5.0
    slider_label.setText(f"Sphere Radius: {slider_value:.2f}")
    print(f"Slider value changed to: {slider_value:.2f}")

# Create a custom widget with slider
slider_widget = QWidget()
slider_layout = QVBoxLayout()

# Create label
slider_label = QLabel(f"Sphere Radius: {slider_value:.2f}")
slider_layout.addWidget(slider_label)

# Create slider (range 1-50, representing 0.1-5.0)
slider = QSlider(Qt.Orientation.Horizontal)
slider.setMinimum(1)
slider.setMaximum(50)
slider.setValue(10)  # Default value 1.0
slider.setTickPosition(QSlider.TickPosition.TicksBelow)
slider.setTickInterval(5)
slider.valueChanged.connect(on_slider_change)
slider_layout.addWidget(slider)

slider_widget.setLayout(slider_layout)

# Create a dock widget for the slider
dock = QDockWidget("Controls", viewer.ui.window.widget)
dock.setWidget(slider_widget)
viewer.ui.window.widget.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

# Create key event for adding spheres
add_event = KeyEvent(title="Add Sphere", key="A")
add_event.triggered.connect(add_sphere)
viewer.eventmanager.key_events.append(add_event)

# Create key event for removing spheres
remove_event = KeyEvent(title="Remove Last Sphere", key="R")
remove_event.triggered.connect(remove_last_sphere)
viewer.eventmanager.key_events.append(remove_event)

print("Controls:")
print("  - Move the slider to change sphere radius")
print("  - Press 'A' to add a sphere with the current radius")
print("  - Press 'R' to remove the last sphere")

# Show the viewer
viewer.show()
