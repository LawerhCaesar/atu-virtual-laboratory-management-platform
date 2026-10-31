"""Run the preserved controller/UI checks through the 2D fallback.
Dedicated test_fuel_visual_review.py and the existing 3D explorer exercise WebGL.
"""
import pytest
import test_fuel_delivery_ui as preserved
pytestmark=preserved.pytestmark
for name in dir(preserved):
 if name.startswith('test_') and '3d' not in name:
  globals()[name]=getattr(preserved,name)

@pytest.fixture(autouse=True)
def logic_fallback(page):
 page.add_init_script("""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'||type==='webgl2'?null:original.call(this,type,...args);};})();""")
