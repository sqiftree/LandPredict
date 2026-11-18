'use strict';
const $=id=>document.getElementById(id);
const fmt=(n,d=0)=>Number(n).toLocaleString('id-ID',{maximumFractionDigits:d});
const definitions={harga_tanah_rata_rata_rp_m2:['Harga tanah rata-rata','Rp/m²'],built_pct:['Proporsi lahan terbangun','%'],cropland_pct:['Proporsi tutupan pertanian','%'],tree_pct:['Proporsi tutupan pohon','%'],kepadatan_penduduk_proksi:['Kepadatan penduduk · proksi','jiwa/km²'],kepadatan_fasum_proksi:['Kepadatan fasilitas · proksi','unit/km²'],worldcover_valid_pct:['Cakupan piksel raster valid','%']};
const colors=['#e8efcd','#b5d4a1','#75ae87','#398574','#17574d'];
const map=L.map('map',{zoomControl:true}).setView([-7.65,110.9],9);
map.attributionControl.addAttribution('Batas BIG · ESA WorldCover 2020 · Lampiran Aziz');
const osm=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'});
let all,polygons,breaks=[],active='harga_tanah_rata_rata_rp_m2',selected=null;
function color(v){let i=0;while(i<4&&v>breaks[i])i++;return colors[i];}
function show(p){selected=p;$('selected').textContent=p.kecamatan;$('details').innerHTML=`<p class="caption">${p.kab_kota} · 2020</p><div class="stats">${[['Harga tanah',fmt(p.harga_tanah_rata_rata_rp_m2)+' Rp/m²'],['Penduduk',fmt(p.jumlah_penduduk)+' jiwa'],['Terbangun',fmt(p.built_pct,2)+'%'],['Pertanian',fmt(p.cropland_pct,2)+'%'],['Pohon',fmt(p.tree_pct,2)+'%'],['Raster valid',fmt(p.worldcover_valid_pct,2)+'%']].map(([a,b])=>`<div><span>${a}</span><b>${b}</b></div>`).join('')}</div><p class="caption">Luas arsip BIG: ${fmt(p.luas_arsip_km2,2)} km². Batas historis 2020 belum terverifikasi. Tidak mewakili harga setiap bidang tanah.</p>`;}
function render(){
 active=$('layer').value;const reg=$('region').value,query=$('search').value.toLowerCase().trim();
 const features=all.features.filter(f=>(!reg||f.properties.kab_kota===reg)&&f.properties.kecamatan.toLowerCase().includes(query));
 // Fixed full-region quantiles keep colors comparable when filters change.
 const values=all.features.map(f=>Number(f.properties[active])).sort((a,b)=>a-b);breaks=[.2,.4,.6,.8].map(q=>values[Math.floor(q*(values.length-1))]);
 if(polygons)map.removeLayer(polygons);
 polygons=L.geoJSON({type:'FeatureCollection',features},{style:f=>({color:'#fff',weight:1,fillColor:color(Number(f.properties[active])),fillOpacity:.85}),onEachFeature:(f,l)=>{const p=f.properties;l.bindTooltip(`${p.kecamatan} · ${fmt(p[active],2)} ${definitions[active][1]}`,{sticky:true});l.on({click:()=>{show(p);map.fitBounds(l.getBounds(),{maxZoom:12,padding:[25,25]});},mouseover:()=>l.setStyle({weight:2,color:'#193b35'}),mouseout:()=>l.setStyle({weight:1,color:'#fff'})});}}).addTo(map);
 $('maptitle').textContent=definitions[active][0];$('count').textContent=`${features.length} / 127 kecamatan`;
 const limits=[values[0],...breaks,values.at(-1)];const unit=definitions[active][1];
 $('legend').innerHTML=`<b>${unit}</b><div class="caption">Kuintil seluruh Solo Raya</div>`+colors.map((c,i)=>`<div class="legend-row"><span class="swatch" style="background:${c}"></span>${i?'&gt; ':''}${fmt(limits[i],2)} – ${fmt(limits[i+1],2)}</div>`).join('')+(values[0]===values.at(-1)?'<div>Seluruh nilai sama.</div>':'');
 if(selected&&!features.some(f=>f.properties.kab_kota===selected.kab_kota&&f.properties.kecamatan===selected.kecamatan)){selected=null;$('selected').textContent='Pilih kecamatan pada peta';$('details').textContent='Klik wilayah untuk melihat angka, cakupan, dan sumbernya.';}
}
function scatter(){const w=400,h=170,x0=45,y0=140,max=Math.max(...all.features.map(f=>Number(f.properties.harga_tanah_rata_rata_rp_m2)));
 $('scatter').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Sebaran proporsi terbangun dan harga tanah 127 kecamatan"><path d="M45 8V140H390" fill="none" stroke="#ccd8cf"/>${[0,50,100].map(v=>`<text x="${x0+v*3.4}" y="158" text-anchor="middle" font-size="9" fill="#667771">${v}%</text>`).join('')}<text x="6" y="14" font-size="9">${fmt(max/1e6,1)} jt</text><text x="15" y="140" font-size="9">0</text>${all.features.map(f=>{const p=f.properties;return `<circle cx="${x0+Number(p.built_pct)*3.4}" cy="${y0-Number(p.harga_tanah_rata_rata_rp_m2)/max*125}" r="3" fill="#398574" opacity=".65"><title>${p.kecamatan}: ${fmt(p.built_pct,2)}%; Rp ${fmt(p.harga_tanah_rata_rata_rp_m2)}/m²</title></circle>`}).join('')}</svg>`;
 $('correlation').textContent='Sumbu X: terbangun (%); Y: harga (Rp/m²). Pola deskriptif, bukan bukti sebab-akibat atau signifikansi.';
}
$('sources').onclick=()=>$('sourceDialog').showModal();$('closeSources').onclick=()=>$('sourceDialog').close();
$('basemap').onchange=e=>e.target.checked?osm.addTo(map):map.removeLayer(osm);
$('layer').onchange=()=>all&&render();$('search').oninput=()=>all&&render();$('region').onchange=()=>{if(!all)return;render();if(polygons.getLayers().length)map.fitBounds(polygons.getBounds(),{padding:[25,25]});};
$('reset').onclick=()=>{if(!all)return;$('region').value='';$('search').value='';render();map.fitBounds(polygons.getBounds(),{padding:[20,20]});};
fetch('solo_raya_display.geojson').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(data=>{all=data;if(all.features.length!==127)throw Error('Jumlah wilayah tidak sesuai');[...new Set(all.features.map(f=>f.properties.kab_kota))].sort().forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r;$('region').append(o);});render();map.fitBounds(polygons.getBounds(),{padding:[20,20]});scatter();}).catch(e=>{$('error').hidden=false;$('error').textContent='Data peta gagal dimuat. Jalankan melalui server HTTP atau buka alamat situs terbit. '+e.message;});
