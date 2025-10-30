from compas_viewer import Viewer
from compas_viewer.events import KeyEvent
from compas.geometry import Sphere, Point, Frame, Line
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

# Stack of added spheres and their companion line objects
added_spheres = []

def add_sphere():
    """Add a sphere with radius controlled by slider."""
    x = random.uniform(-5, 5)
    y = random.uniform(-5, 5)
    z = random.uniform(-5, 5)
    
    # Use slider_value for the sphere radius
    frame = Frame(Point(x, y, z))
    sphere = Sphere(radius=slider_value, frame=frame)
    sphere_obj = viewer.scene.add(sphere, name=f"Sphere_{slider_value:.2f}")

    sphere_obj.init()
    viewer.renderer.buffer_manager.add_object(sphere_obj)

    line_objs = []
    for idx in range(3):
        start = Point(random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5))
        end = Point(random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5))
        line = Line(start, end)
        line_obj = viewer.scene.add(line, name=f"Line_{idx + 1}")
        line_obj.init()
        viewer.renderer.buffer_manager.add_object(line_obj)
        line_objs.append(line_obj)

    added_spheres.append({"sphere": sphere_obj, "lines": line_objs})
    viewer.renderer.buffer_manager.create_buffers()
    
    # Force a repaint of the viewport
    viewer.renderer.update()
    viewer.ui.sidebar.update()
    print(
        f"Added sphere at ({x:.2f}, {y:.2f}, {z:.2f}) with radius {slider_value:.2f} and {len(line_objs)} lines"
    )

def remove_last_sphere():
    """Remove the last added sphere."""
    if not added_spheres:
        print("Only initial sphere left, cannot remove.")
        return

    record = added_spheres.pop()
    sphere_obj = record["sphere"]
    line_objs = record["lines"]

    for line_obj in line_objs:
        print(f"Removing line: {line_obj.name}")
        viewer.scene.remove(line_obj)

    print(f"Removing sphere: {sphere_obj.name}")
    viewer.scene.remove(sphere_obj)

    # Clear and rebuild the buffer manager to reflect removals
    viewer.renderer.buffer_manager.clear()
    viewer.renderer.buffer_manager.objects.clear()

    for scene_obj in viewer.scene.objects:
        viewer.renderer.buffer_manager.add_object(scene_obj)

    viewer.renderer.buffer_manager.create_buffers()
    print(
        f"Recreated buffers. Remaining spheres: {len(added_spheres)} plus initial, lines removed: {len(line_objs)}"
    )

    viewer.renderer.update()
    viewer.ui.sidebar.update()

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
