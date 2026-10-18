"""Test the actual GNOME constructor wrapper without changing a live Shell."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Node required for the JS harness')
class WindowPreviewTests(unittest.TestCase):
    def test_resize_modes_dpi_and_restore(self):
        result = subprocess.run(['node', '--input-type=module', '-'], input=HARNESS,
                                cwd=ROOT, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


HARNESS = r'''
import fs from 'node:fs';
import assert from 'node:assert/strict';
class Actor { set_size(w,h){this.width=w;this.height=h;} }
class Clone extends Actor { constructor(w,h){super();this.source={get_size:()=>[w,h]};} }
class WindowIcon {
 _init(w,h,mode){
  this.originalCalled=true;
  this.appIcon={width:48,height:48};
  this._icon=new Actor();
  this.clone=new Clone(w,h);
  this._icon.get_children=()=>mode==='icon'?[this.appIcon]:[this.clone,this.appIcon];
  this._icon.set_size(mode==='icon'?96:128,mode==='icon'?96:128);
 }
}
const original=WindowIcon.prototype._init;
class InjectionManager {
 overrideMethod(proto,key,factory){this.undo=()=>proto[key]=original;proto[key]=factory(proto[key]);}
 clear(){this.undo();}
}
let factor=1;
const St={ThemeContext:{get_for_stage:()=>({scale_factor:factor})}};
const source=fs.readFileSync('alt-tab-extension/extension.js','utf8')
 .replace(/^import .*;\n/gm,'').replace('export default class LargerWindowPreviews extends Extension','return class LargerWindowPreviews extends Extension');
const Type=new Function('Clutter','St','Extension','InjectionManager','AltTab','global',source)
 ({Clone},St,class {},InjectionManager,{WindowIcon},{stage:{}});
const extension=new Type();extension.enable();
function make(w,h,mode='both'){const icon=new WindowIcon();icon._init(w,h,mode);assert(icon.originalCalled);return icon;}
let icon=make(1920,1080);assert.equal(icon.clone.width,192);assert.equal(icon.clone.height,108);assert.equal(icon._icon.width,192);assert.equal(icon.appIcon.width,48);
icon=make(800,1200,'thumbnail');assert.equal(icon.clone.width,128);assert.equal(icon.clone.height,192);
factor=2;icon=make(1920,1080);assert.equal(icon.clone.width,384);assert.equal(icon.clone.height,216);assert.equal(icon._icon.width,384);
factor=1;icon=make(100,50);assert.equal(icon.clone.width,100);assert.equal(icon.clone.height,50);
icon=make(1920,1080,'icon');assert.equal(icon._icon.width,96);
icon=make(0,0);assert.equal(icon.clone.width,undefined);
extension.disable();assert.equal(WindowIcon.prototype._init,original);
icon=make(1920,1080);assert.equal(icon._icon.width,128);
extension.disable();
console.log('Window preview behavior OK');
'''
