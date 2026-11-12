/* El archivo del usuario se entrega a este worker en memoria; nunca a una URL. */
const RUNTIME='https://cdn.jsdelivr.net/pyodide/v0.29.3/full/';
let motor;
const progress=message=>postMessage({type:'progress',message});
async function iniciar(){
  if(motor) return motor;
  progress('Cargando el motor estadístico. La primera vez puede tardar varios minutos…');
  importScripts(RUNTIME+'pyodide.js');
  const py=await loadPyodide({indexURL:RUNTIME});
  progress('Preparando las bibliotecas de análisis…');
  await py.loadPackage(['pandas','scipy','statsmodels','micropip']);
  await py.runPythonAsync("import micropip\nawait micropip.install('openpyxl==3.1.5')");
  py.FS.mkdirTree('/app');
  for(const file of ['esquema.py','comun.py','analisis_doctoral.py','analisis_pregrado.py','configuracion.json','redaccion.py','aplicacion.py']){
    const r=await fetch('engine/'+file); if(!r.ok)throw Error('No se pudo cargar '+file);
    py.FS.writeFile('/app/'+file,await r.text());
  }
  await py.runPythonAsync("import sys\nsys.path.insert(0,'/app')\nfrom aplicacion import ejecutar_archivo");
  motor=py;return py;
}
onmessage=async({data})=>{
  try{
    const py=await iniciar(); progress('Revisando la base y calculando los dos análisis…');
    py.globals.set('contenido_js',new Uint8Array(data.buffer));
    py.globals.set('nombre_js',data.name);py.globals.set('diseno_js',data.design);py.globals.set('demo_js',data.demo);
    const respuesta=await py.runPythonAsync("resultado_json, resultado_zip = ejecutar_archivo(bytes(contenido_js.to_py()), nombre_js, diseno_js, demo_js)\nresultado_json");
    const z=py.globals.get('resultado_zip');const bytes=z.toJs();z.destroy();
    postMessage({type:'result',result:JSON.parse(respuesta),zip:bytes},[bytes.buffer]);
    py.runPython("del contenido_js, resultado_zip, resultado_json");
  }catch(e){
    const detalle=String(e.message||e);postMessage({type:'error',message:detalle});
  }
};
