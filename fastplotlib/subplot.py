import pygfx
from pygfx import Scene, OrthographicCamera, PerspectiveCamera, PanZoomController, Viewport, AxesHelper, GridHelper
from .defaults import camera_types, controller_types
from typing import *
from wgpu.gui.auto import WgpuCanvas
from warnings import warn


class Subplot:
    def __init__(
            self,
            position: Tuple[int, int] = None,
            parent_dims: Tuple[int, int] = None,
            camera: str = '2d',
            controller: Union[pygfx.PanZoomController, pygfx.OrbitOrthoController] = None,
            canvas: WgpuCanvas = None,
            renderer: pygfx.Renderer = None
    ):
        self.scene: pygfx.Scene = pygfx.Scene()

        if canvas is None:
            canvas = WgpuCanvas()

        if renderer is None:
            renderer = pygfx.renderers.WgpuRenderer(canvas)

        self.canvas = canvas
        self.renderer = renderer

        if position is None:
            position = (0, 0)
        self.position: Tuple[int, int] = position

        if parent_dims is None:
            parent_dims = (1, 1)

        self.nrows, self.ncols = parent_dims

        self.camera: Union[pygfx.OrthographicCamera, pygfx.PerspectiveCamera] = camera_types[camera]()

        if controller is None:
            controller = controller_types[camera]()
        self.controller: Union[pygfx.PanZoomController, pygfx.OrbitOrthoController] = controller

        # might be better as an attribute of GridPlot
        # but easier to iterate when in same object as camera and scene
        self.viewport: pygfx.Viewport = pygfx.Viewport(renderer)

        self.controller.add_default_event_handlers(
            self.viewport,
            self.camera
        )

        self._axes: AxesHelper = AxesHelper(size=100)
        for arrow in self._axes.children:
            self._axes.remove(arrow)

        self._grid: GridHelper = GridHelper(size=100, thickness=1)

        self._animate_funcs = list()

        self.renderer.add_event_handler(self._produce_rect, "resize")

    def _produce_rect(self, *args):#, w, h):
        i, j = self.position

        w, h = self.renderer.logical_size

        spacing = 0  # spacing in pixels

        self.viewport.rect = [
            ((w / self.ncols) + ((j - 1) * (w / self.ncols))) + spacing,
            ((h / self.nrows) + ((i - 1) * (h / self.nrows))) + spacing,
            (w / self.ncols) - spacing,
            (h / self.nrows) - spacing
        ]

    def animate(self, canvas_dims: Tuple[int, int] = None):
        self.controller.update_camera(self.camera)
        self.viewport.render(self.scene, self.camera)

        for f in self._animate_funcs:
            f()

    def add_animations(self, funcs: List[callable]):
        self._animate_funcs += funcs

    def add_graphic(self, graphic, center: bool = True):
        self.scene.add(graphic.world_object)

        if center:
            self.center_scene()

    def center_graphic(self):
        pass

    def center_scene(self, zoom: float = 1.3):
        if not isinstance(self.camera, pygfx.OrthographicCamera):
            warn("`center_scene()` not yet implemented for `PerspectiveCamera`")
            return

        self.controller.update_camera(self.camera)
        self.camera.set_view_size(1, 1)
        self.camera.update_projection_matrix()

        self.controller.show_object(self.camera, self.scene)

        self.controller.zoom(zoom)

    def set_axes_visibility(self, visible: bool):
        if visible:
            self.scene.add(self._axes)
        else:
            self.scene.remove(self._axes)

    def set_grid_visibility(self, visible: bool):
        if visible:
            self.scene.add(self._grid)
        else:
            self.scene.remove(self._grid)

    def remove_graphic(self, graphic):
        self.scene.remove(graphic.world_object)