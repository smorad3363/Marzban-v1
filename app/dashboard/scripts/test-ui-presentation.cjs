const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const css = fs.readFileSync(path.join(root, 'src/index.scss'), 'utf8');
const luminosity = hex => {
  const rgb = [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
  return rgb.reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
};
const contrast = (a,b) => { a=luminosity(a);b=luminosity(b);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05); };
const regions = [css.slice(css.indexOf(':root,'), css.indexOf('.chakra-ui-dark {')), css.slice(css.indexOf('.chakra-ui-dark {'), css.indexOf('html {'))];
let checks=0;
for(const [index,region] of regions.entries()) {
  const colors=Object.fromEntries([...region.matchAll(/--panel-([\w-]+): (#[\da-f]{6});/g)].map(m=>[m[1],m[2]]));
  for(const text of ['text','text-body','text-muted','accent','success','warning','danger','info']) {
    for(const background of ['bg','surface','input','nested']) {
      const ratio=contrast(colors[text],colors[background]);
      assert.ok(ratio>=4.5,`${index?'Black':'White'}: ${text} on ${background} contrast ${ratio.toFixed(2)} < 4.5`);checks++;
    }
  }
  assert.ok(contrast(colors.accent,colors['accent-contrast'])>=4.5,'Primary button text must remain readable');checks++;
  assert.ok(contrast(colors['border-strong'],colors.input)>=3,'Input boundaries must have at least 3:1 contrast');checks++;
}
assert.ok(!css.includes('fonts.googleapis.com'),'Fonts must not depend on a remote stylesheet');
for(const file of ['vazirmatn-arabic.woff2','inter-latin.woff2','vazirmatn-LICENSE.txt','inter-LICENSE.txt']) assert.ok(fs.statSync(path.join(root,'public/statics/fonts',file)).size>1000,'Local licensed font missing');
assert.ok(css.includes('prefers-reduced-motion') && css.includes('(pointer: coarse)') && css.includes('(hover: hover)'),'Responsive motion and touch rules must be present');
console.log(`UI presentation: ${checks} light/dark contrast checks, local fonts and input accessibility passed`);
