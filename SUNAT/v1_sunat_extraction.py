import requests
import os
import re
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---

# Pega aquí el contenido completo del archivo HTML que obtuviste.
# Es importante que sea el HTML completo de la página que contiene los enlaces.
HTML_CONTENT = """

 

<html>
<head>
	<title>Consulta de subpartidas y Resoluciones de Clasificacion Arancelaria</title>
	<link href="/a/css/estilos2_0.css" rel="stylesheet" type="text/css">
	
	
		
</head>

<script language="JavaScript" src="/a/js/js.js"></script>
<script language="JavaScript" src="/a/js/Utils.js"></script>
<script language="JavaScript1.2" src="/a/js/paginacion.js"></script>
<script language="JavaScript">
	function buscar(){
		var f = document.frmBusqueda;	
		
		if ( trim(f.txtValor.value)==""){
			if(f.cmbCriterio.value != "0"){
				alert("Debe ingresar un texto de búsqueda");
				f.txtValor.focus();
				return false;
			}
		}
		
		if(f.cmbCriterio.value == "1"){//si se busca por subpartida se formatea el texto a buscar
		    for(var i=1; i<=3;i++){
		    	f.txtValor.value = f.txtValor.value.replace('.',''); //elimina los (.) en la txtValor (cadena de subpartida)
		    }
		}
		
		if(f.cmbCriterio.value == "2"){//se formatea a mayusculas el texto a buscar
		    if(f.txtValor.value.length < 3){
			    alert("Debe ingresar un texto de búsqueda mayor o igual a tres dígitos");
			    f.txtValor.select();
			    return false;
		    }else{
		    	f.txtValor.value = f.txtValor.value.toUpperCase();
		    }
		}
		if(f.cmbCriterio.value == "3"){//si se busca por nro. de resolucion se formatea el texto a buscar
		    f.txtValor.value = rellena(f.txtValor.value,'0',6);
		}
	}
	
	function cambiarSeleccion(){
		var f = document.frmBusqueda;
		if(f.cmbCriterio.value != "2"){
			f.txtValor.value = "";
		}
		if(f.cmbCriterio.value == "2"){
			f.txtValor.value = "<Mínimo tres dígitos>";
			f.txtValor.select();
		}
		f.txtValor.focus();
	}
	
	
	function muestraResolucion(pImg) {
		
		ventana_secundaria = window.open('/descarga-ad/aduanas/res_clas/' + pImg,'Resolucion','');
	}
	
	function jsDescargarArchivo(cod_tipclas, num_resclas, fano_resclas) {
		//Invocar al metodo ServletRegiClasificacion.descargarArchivo();      
	  	f = document.frmPortal;
	  	f.cod_tipclas.value = cod_tipclas;
			f.num_resclas.value = num_resclas;
			f.fano_resclas.value = fano_resclas;
		  f.accion.value = "descargarArchivo";
		  f.submit();		  
	}
	
	
</script>


<body>
<TABLE class="form-table" cellSpacing="2" cellPadding="3" width="95%" align="center">
  <TR><TD class="T1" align="center">Consulta de Resoluciones de Clasificación Arancelaria</TD></TR>
</TABLE>





<TABLE><TR><TD>

<br>
<form name="frmBusqueda" method="post" action="/ol-ad-caInter/regclasInterS01Alias" onSubmit="return buscar();">
<input type="hidden" id="accion" name="accion" value="cargarSubpartidas">

     <!-- hiddens como clave primaria para hacer el mantenimiento al objeto seleccionado-->
          <input type="hidden" name="cod_tipclas" value="">
          <input type="hidden" name="num_resclas" value="">
          <input type="hidden" name="fano_resclas" value="">
      <!-- fin -->

<table class="form-table" width="95%" border="0" cellpadding="0" cellspacing="0" align="center">
  <tr><td></td></tr>
  <tr>
  	<td colspan="6">
  	Esta opción permite consultar las Resoluciones de Intendencia Nacional 
	que muestra la clasificación de mercancías. Inicialmente se listan los 30 últimos registros de Resoluciones emitidas y 
	si desea buscar una Resolución específica puede seleccionar un criterio e ingresar el texto del 
	criterio a buscar.
	<br><br>
		<FONT FACE="Arial" SIZE="1" COLOR="#0033FF">
		<b><u>NOTA IMPORTANTE:</u></b><br>
		<b>
		La resolución de clasificación arancelaria es válida durante la vigencia del arancel de aduanas con el cual se clasificó
		la mercancía, siempre que no se produzcan modificaciones en la subpartida nacional, o por las siguientes causales:<br>
		a) La resolución contenga errores materiales o sustanciales.<br>
		b) Se produzca un cambio de los hechos, información o documentación en la que se sustentó su emisión.<br>
		c) Otras situaciones a criterio de la SUNAT, debidamente fundamentadas.
		</b>
		</FONT>
	</td>
  </tr>	
  
  <tr><td colspan="6"><hr color="#007BA4" size="1"></td></tr>
  <tr>
	<td align="center">Buscar por: </td>
	<td align="center"> 
		<select name="cmbCriterio" id="cmbCriterio" class="bg" onChange="javascript:cambiarSeleccion()">
			<option value="0">.. Todos ..</option>
			<option value="1">Nro. de Subpartida</option>
			<option value="2">Descripción</option>
			<option value="3">Nro. de la Resol de Clasif</option>
		</select>
	</td>
	<td><input type="text" id="txtValor" name="txtValor" size="20" value="" class="form-text"></td>
	<td align="center">Ordenado por: </td>
	<td>
		<select name="cmbOrderBy" id="cmbOrderBy" class="bg">
			<option value="0"></option>
			<option value="1">Nro. de Subpartida</option>
			<option value="2">Descripción</option>
			<option value="3">Nro. de la Resol de Clasif</option>
			<option value="4">Fecha de publicación</option>
		</select>
	</td>
	<td>
		<input name="submit" type="submit" class="form-button" value=" Buscar ">&nbsp;&nbsp;&nbsp;
	</td>
  </tr>
  <tr><td>&nbsp;</td></tr>	
</table>
</form>

<form name="frmPortal" method="post" action="/ol-ad-caInter/regclasInterS01Alias">
          <input type="hidden" id="accion" name="accion" value="">
	    <!-- hiddens como clave primaria para hacer el mantenimiento al objeto seleccionado-->
          <input type="hidden" name="cod_tipclas" value="">
          <input type="hidden" name="num_resclas" value="">
          <input type="hidden" name="fano_resclas" value="">
      <!-- fin -->
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
Nro. total de registros: <b>6112
<table cellspacing="2" cellpadding="3" border="0" width="95%" align="center" class="form-table">
<tr>	
	<td>	
    
	






    <table border="0" cellspacing="0" width="100%">
	<tr>
		<td class="lnk7" align="right"  width="50%">
			
			
				1
			
			 	a 30 de 6106
		</td>
	</tr>
</table>
<table width="100%" cellspacing="0">
<tr>
	<td align="left" width="10%" class="lnk7">
		
	</td>
	<td align="center" class="lnk7">
		
				P&aacute;ginas:
				
					
						1 | 
					
				
					
						<a href="javascript:paginacion(30,1)">2 | </a>
					
				
					
						<a href="javascript:paginacion(30,2)">3 | </a>
					
				
					
						<a href="javascript:paginacion(30,3)">4 | </a>
					
				
					
						<a href="javascript:paginacion(30,4)">5 | </a>
					
				
					
						<a href="javascript:paginacion(30,5)">6 | </a>
					
				
					
						<a href="javascript:paginacion(30,6)">7 | </a>
					
				
					
						<a href="javascript:paginacion(30,7)">8 | </a>
					
				
					
						<a href="javascript:paginacion(30,8)">9 | </a>
					
				
					
						<a href="javascript:paginacion(30,9)">10 | </a>
					
				
					
						<a href="javascript:paginacion(30,10)">11 | </a>
					
				
					
						<a href="javascript:paginacion(30,11)">12 | </a>
					
				
					
						<a href="javascript:paginacion(30,12)">13 | </a>
					
				
					
						<a href="javascript:paginacion(30,13)">14 | </a>
					
				
					
						<a href="javascript:paginacion(30,14)">15 | </a>
					
				
					
						<a href="javascript:paginacion(30,15)">16 | </a>
					
				
					
						<a href="javascript:paginacion(30,16)">17 | </a>
					
				
					
						<a href="javascript:paginacion(30,17)">18 | </a>
					
				
					
						<a href="javascript:paginacion(30,18)">19 | </a>
					
				
					
						<a href="javascript:paginacion(30,19)">20 | </a>
					
				
					
						<a href="javascript:paginacion(30,20)">21 | </a>
					
				
					
						<a href="javascript:paginacion(30,21)">22 | </a>
					
				
					
						<a href="javascript:paginacion(30,22)">23 | </a>
					
				
					
						<a href="javascript:paginacion(30,23)">24 | </a>
					
				
					
						<a href="javascript:paginacion(30,24)">25 | </a>
					
				
					
						<a href="javascript:paginacion(30,25)">26 | </a>
					
				
					
						<a href="javascript:paginacion(30,26)">27 | </a>
					
				
					
						<a href="javascript:paginacion(30,27)">28 | </a>
					
				
					
						<a href="javascript:paginacion(30,28)">29 | </a>
					
				
					
						<a href="javascript:paginacion(30,29)">30 | </a>
					
				
					
						<a href="javascript:paginacion(30,30)">31 | </a>
					
				
					
						<a href="javascript:paginacion(30,31)">32 | </a>
					
				
					
						<a href="javascript:paginacion(30,32)">33 | </a>
					
				
					
						<a href="javascript:paginacion(30,33)">34 | </a>
					
				
					
						<a href="javascript:paginacion(30,34)">35 | </a>
					
				
					
						<a href="javascript:paginacion(30,35)">36 | </a>
					
				
					
						<a href="javascript:paginacion(30,36)">37 | </a>
					
				
					
						<a href="javascript:paginacion(30,37)">38 | </a>
					
				
					
						<a href="javascript:paginacion(30,38)">39 | </a>
					
				
					
						<a href="javascript:paginacion(30,39)">40 | </a>
					
				
					
						<a href="javascript:paginacion(30,40)">41 | </a>
					
				
					
						<a href="javascript:paginacion(30,41)">42 | </a>
					
				
					
						<a href="javascript:paginacion(30,42)">43 | </a>
					
				
					
						<a href="javascript:paginacion(30,43)">44 | </a>
					
				
					
						<a href="javascript:paginacion(30,44)">45 | </a>
					
				
					
						<a href="javascript:paginacion(30,45)">46 | </a>
					
				
					
						<a href="javascript:paginacion(30,46)">47 | </a>
					
				
					
						<a href="javascript:paginacion(30,47)">48 | </a>
					
				
					
						<a href="javascript:paginacion(30,48)">49 | </a>
					
				
					
						<a href="javascript:paginacion(30,49)">50 | </a>
					
				
			
	</td>
	<td align="right" width="10%" class="lnk7">
		<a href="javascript:paginacion(30,1)">Siguiente</a>
	</td>
</tr>
</table>  
	<table cellpadding="0" cellspacing="0" width="100%">
	<tbody>
	<tr>
	<td class="beta">
		<table cellspacing="1" cellpadding="1" width="100%" align="center">		
		<tbody>
			<tr align="center">
				<th width="15%" class="beta">Subpartida</th>
				<th width="50%" class="beta">Descripción</th>
				<th width="15%" class="beta">Resolución</th>
				<th width="15%" class="beta">Fecha<br> Publicación</th>
				<th width="5%" class="beta"></th>
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					8517.13.00.00	
				</td>
				<td> TELEFONO DE PULSERA ¿ ULTRA KING IA3. UNIDAD. TELECOMUNICACIONES
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_380_2025_PUBLI.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_380_2025_PUBLI.pdf')">R-000380-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000380','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000380','2025')"%>R-000380-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					24/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"><b>(Nuevo)</b></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					6404.19.00.00	
				</td>
				<td> SANDALIA FOOTLOOSE MODELO: FTL-NZ00004. EN CAJA. CASUAL
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD 373 2025.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD 373 2025.pdf')">R-000373-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000373','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000373','2025')"%>R-000373-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					24/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"><b>(Nuevo)</b></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2008.99.90.00	
				</td>
				<td> MEZCLA DE UVA CON RECUBRIMIENTO AGRIO CONGELADO. BOLSA. CONSUMO HUMANO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_370_2025_PUB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_370_2025_PUB.pdf')">R-000370-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000370','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000370','2025')"%>R-000370-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					24/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"><b>(Nuevo)</b></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3824.99.99.99	
				</td>
				<td> MICROPLUS. GALONERA DE 1L Y 20L. NUTRIENTE ESTIMULANTE
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_374_2025_PUB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_374_2025_PUB.pdf')">R-000374-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000374','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000374','2025')"%>R-000374-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					24/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"><b>(Nuevo)</b></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3824.99.99.99	
				</td>
				<td> ATRAYENTE DE ABEJAS APIS BLOOM. EN TUBOS DE 250 Y 750 G. ATRAYENTE DE ABEJAS
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_375_2025_PUB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_375_2025_PUB.pdf')">R-000375-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000375','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000375','2025')"%>R-000375-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					24/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"><b>(Nuevo)</b></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3926.90.90.90	
				</td>
				<td> GEOCOMPUESTO DE DRENAJE. ROLLOS. RETENCIÓN DE PARTÍCULAS DEL SUELO Y FILTRACIÓN EN TERRAPLENES, MINERÍA, VERTEDEROS
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('3926RD2025363p.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('3926RD2025363p.pdf')">R-000363-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000363','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000363','2025')"%>R-000363-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					18/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3824.99.99.99	
				</td>
				<td> TRIPTO L. A GRANEL. AGRICOLA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RESDIV_360_2025.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RESDIV_360_2025.pdf')">R-000360-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000360','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000360','2025')"%>R-000360-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					15/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2008.99.30.00	
				</td>
				<td> MANGO CHIPS. ENVASE. CONSUMO HUMANO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('313300_2025_358.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('313300_2025_358.pdf')">R-000358-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000358','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000358','2025')"%>R-000358-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					15/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					6404.19.00.00	
				</td>
				<td> ZAPATILLAS, DE MARCA COMERCIAL: R18, MODELO: R18- MG00275. CAJA. CALZADO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RESDIV_2025_362_.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RESDIV_2025_362_.pdf')">R-000362-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000362','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000362','2025')"%>R-000362-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					15/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3916.90.00.00	
				</td>
				<td> POLIONDA CAVASER. EN UNIDADES. INDUSTRIAL
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD319_web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD319_web.pdf')">R-000319-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000319','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000319','2025')"%>R-000319-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					14/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					1806.32.00.00	
				</td>
				<td> TRITURADOR DE CARBOHIDRATOS. BARRA. TRITURADOR DE CARBOHIDRATOS A BASE DE PLANTAS
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RESDIV_2025_359_.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RESDIV_2025_359_.pdf')">R-000359-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000359','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000359','2025')"%>R-000359-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					14/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3906.90.90.00	
				</td>
				<td> MAGNAFLOC¿ 351 AP. SACOS DE 25 KG, Y BIG BAG.. PRODUCTO QUÍMICO INDUSTRIAL EN DIVERSAS OPERACIONES DE PROCESAMIENTO DE MINERALES.
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_357_2025.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_357_2025.pdf')">R-000357-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000357','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000357','2025')"%>R-000357-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					14/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					1901.10.99.00	
				</td>
				<td> ENFAGROW Æ PREMIUM PROMENTAL CONFORT PRO ¿ ETAPA CRECIMIENTO 2. LATA DE 800 GRAMOS. MEZCLA EN POLVO PARA RECONSTITUCIÓN PARA NIÑOS EN CRECIMIENTO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD352PUB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD352PUB.pdf')">R-000352-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000352','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000352','2025')"%>R-000352-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					14/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					9106.10.00.00	
				</td>
				<td> INVIXIUM TITAN ADVANCE ¿ CONTROL BIOMÉTRICO. UNIDAD. REGISTRO DE ACCESO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_365_2025_PUBLI.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_365_2025_PUBLI.pdf')">R-000365-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000365','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000365','2025')"%>R-000365-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					14/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					6310.10.10.00	
				</td>
				<td> TRAPO INDUSTRIAL. KILOGRAMOS. LIMPIEZA (POLVO Y SUCIEDAD DE ESPACIOS, LIMPIAR MUEBLES, MÁQUINAS Y PISOS).
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_364p.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_364p.pdf')">R-000364-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000364','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000364','2025')"%>R-000364-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					11/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					1806.90.00.00	
				</td>
				<td> CHOCOPERA BITES. TUBO DE CARTÓN, REVESTIMIENTO DE ALUMINIO, BASE METÁLICA, TAPA DE PLÁSTICO, SELLO DE ALUMI. CONSUMO HUMANO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_361P.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_361P.pdf')">R-000361-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000361','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000361','2025')"%>R-000361-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					10/07/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3901.30.00.00	
				</td>
				<td> EVAPOL HFRR 2071 NAT. EN FORMA DE PELLETS. RECUBRIMIENTO DE CABLES
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD39web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD39web.pdf')">R-000039-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000039','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000039','2025')"%>R-000039-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					30/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2916.19.90.00	
				</td>
				<td> UNDECYLENIC ACID. EN UNIDADES. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD124web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD124web.pdf')">R-000124-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000124','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000124','2025')"%>R-000124-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					30/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2941.50.00.00	
				</td>
				<td> CLARITHROMYCIN IDENTITY. EN UNIDADES. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD_125web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD_125web.pdf')">R-000125-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000125','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000125','2025')"%>R-000125-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					30/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2937.22.20.00	
				</td>
				<td> DESOXIMETASONE. EN UNIDADES. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD199.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD199.pdf')">R-000199-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000199','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000199','2025')"%>R-000199-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					30/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2934.99.90.00	
				</td>
				<td> FURAZOLIDONE. EN UNIDADES. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD159WEB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD159WEB.pdf')">R-000159-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000159','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000159','2025')"%>R-000159-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					30/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2846.90.00.00	
				</td>
				<td> GADOPENTETATE MONOMEGLUMINE¿,. EN UNIDADES. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD126web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD126web.pdf')">R-000126-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000126','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000126','2025')"%>R-000126-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					30/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					1605.21.00.00	
				</td>
				<td> LANGOSTINO COCIDO CONGELADO. BANDEJA CIRCULAR DE 170 GRAMOS. CONSUMO HUMANO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD2025_339.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD2025_339.pdf')">R-000339-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000339','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000339','2025')"%>R-000339-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3901.20.00.00	
				</td>
				<td> HIGH DENSITY POLYETHYLENE. EN UNIDADES. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD158WEB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD158WEB.pdf')">R-000158-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000158','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000158','2025')"%>R-000158-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3105.90.90.00	
				</td>
				<td> STEIGER MADURADOR. EN UNIDADES. AGRICULTURA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD90WEB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD90WEB.pdf')">R-000090-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000090','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000090','2025')"%>R-000090-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3808.91.19.00	
				</td>
				<td> PALMERA GEL CUCARACHICIDA Y HORMIGUICIDA. JERINGAS DE 12 GRAMOS. INSECTICIDA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RESOLUC01WEB.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RESOLUC01WEB.pdf')">R-000001-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000001','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000001','2025')"%>R-000001-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2932.99.90.00	
				</td>
				<td> MONOLEATO DE SORBITÁN (SPAK-80). EN UNIDADES. SE UTILIZA EN EXPLOSIVOS, EMULSIÓN, POLIMERIZACIÓN EN EMULSIÓN Y COMO EMULSIONANTE
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RESOLU06_web_total.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RESOLU06_web_total.pdf')">R-000006-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000006','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000006','2025')"%>R-000006-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					3808.94.99.00	
				</td>
				<td> HALQUINOL. EN TAMBORES DE 25 KG. INSUMO PARA LA ELABPARA LA ELABORACIÓN DE PRODUCTOS ANTIBIÓTICOS DE USO VETERINARIO
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD31web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD31web.pdf')">R-000031-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000031','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000031','2025')"%>R-000031-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					6402.91.00.00	
				</td>
				<td> BOTIN CASUAL PARA MUJER. EN UNIDADES. CALZADO PARA DAMA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD58web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD58web.pdf')">R-000058-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000058','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000058','2025')"%>R-000058-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
			<tr align="left" class="bg">
				<td align="center">
					
					2208.90.10.00	
				</td>
				<td> ALCOHOL DETERMINATION - ALCOHOL. EN PRESENTACIONES DE 5 X 5 ML. ESTÁNDAR DE REFERENCIA
				</td>
				<td align="center">
					<!-- ini-wtaco -->
          <!--<img src="/a/imagenes/documents.gif" border="0" onClick="muestraResolucion('RD18web.pdf')" style="cursor:hand"> -->
					<!--<a onClick="muestraResolucion('RD18web.pdf')">R-000018-2025</a>-->
				  
				  <img src="/a/imagenes/documents.gif" border="0" onClick="jsDescargarArchivo('R','000018','2025')" style="cursor:hand">
				  <a onClick="jsDescargarArchivo('R','000018','2025')"%>R-000018-2025</a>
          <!-- fin-wtaco -->
        </td>
				<td align="center">
					
					27/06/2025
				</td>
				<td align="center">
					
					<FONT COLOR="#FF6600"></FONT>
				</td>
				
			</tr>
		
		</tbody>
		</table>	
	</td>
	</tr>
	</tbody>
	</table>
	<br><br>
	</td>
</tr>
</form>	

<BR><BR>
<TABLE cellSpacing="0" cellPadding="5" width="95%" align="center">
  <TBODY><TR><TD><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html><head><title>PiePagina</title></head>

<style>
/* Formato para los comentarios */
BODY{font-size: 8pt;color: black;font-family:"Arial","Verdana","Tahoma","Helvetica",sans-serif;}
.comm   {font-style: italic;font-size: 9pt }
</style>
<body>
<br>
<div align="CENTER">
<ADDRESS>
  <font class="comm">Para cualquier sugerencia sobre el sitio web, por favor comuníquese con:<br>
  <IMG height=32 src="/a/imagenes/lgcorreo.gif" width=32> <A href="mailto:Webmaster@sunat.gob.pe">Webmaster@sunat.gob.pe</A>
  </font> 
</ADDRESS>
<address>
  
  <font class="comm">Copyright © SUNAT 1997 - 2025</font><br>
</address>
</div>
<table border="0" width="100%" cellspacing="0" cellpadding="0">
<tr><td width="100%"><p align="right"><a href="http://www.sunat.gob.pe" target="_blank"><IMG alt=Inicio src="/a/imagenes/sunatpc.jpg" align=bottom border=0></a></p></td></tr>
</table>
</body>
</html>
</TD></TR></TBODY>
</TABLE>	
</body>
</html>
<FORM method="POST" name="formPaginacion" action="/ol-ad-caInter/CAConsultaSubpartidasInter.jsp">
	<INPUT type="hidden" name="tamanioPagina"><INPUT type="hidden" name="pagina">
</FORM>
<FORM action="/ol-ad-caInter/CAConsultaSubpartidasInter.jsp" method="POST" id="NavigFormNext" name="NavigFormNext">
	<INPUT type="hidden" name="currPage" Value = "1"><INPUT type="hidden" name="Action" Value = "next">
</FORM>
<FORM action="/ol-ad-caInter/CAConsultaSubpartidasInter.jsp" method="POST" id="NavigFormBack" name="NavigFormBack">
<INPUT type="hidden" name="currPage" Value = "0"><INPUT type="hidden" name="Action" Value = "back" >
</FORM>
"""

# URL a la que el formulario envía la solicitud. Se obtiene del atributo 'action' del <form name="frmPortal">.
POST_URL = "http://www.aduanet.gob.pe/ol-ad-caInter/regclasInterS01Alias"

# Nombre de la carpeta donde se guardarán los PDFs.
DOWNLOAD_DIR = "resoluciones_sunat"

# --- FIN DE LA CONFIGURACIÓN ---


def descargar_resoluciones():
    """
    Función principal para analizar el HTML y descargar los archivos PDF.
    """
    print("Iniciando el proceso de descarga...")

    # 1. Crear el directorio de descargas si no existe.
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Directorio '{DOWNLOAD_DIR}' creado.")

    # 2. Analizar el HTML con BeautifulSoup.
    soup = BeautifulSoup(HTML_CONTENT, 'html.parser')

    # 3. Encontrar todos los enlaces que ejecutan la función de descarga.
    # Buscamos etiquetas <a> cuyo atributo 'onclick' comience con "jsDescargarArchivo".
    download_links = soup.find_all(
        'a',
        onclick=lambda x: x and x.startswith("jsDescargarArchivo")
    )

    if not download_links:
        print("No se encontraron enlaces de descarga. Verifica el HTML proporcionado.")
        return

    print(f"Se encontraron {len(download_links)} resoluciones para descargar en esta página.")

    # 4. Iterar sobre cada enlace para extraer datos y descargar.
    for link in download_links:
        onclick_attr = link.get('onclick', '')
        
        # 5. Usar una expresión regular para extraer los parámetros de la función JS.
        match = re.search(r"jsDescargarArchivo\('([^']*)','([^']*)','([^']*)'\)", onclick_attr)
        
        if match:
            cod_tipclas, num_resclas, fano_resclas = match.groups()
            
            # Construir el nombre del archivo y el payload para la solicitud POST.
            filename = f"{cod_tipclas}-{num_resclas}-{fano_resclas}.pdf"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            payload = {
                'accion': 'descargarArchivo',
                'cod_tipclas': cod_tipclas,
                'num_resclas': num_resclas,
                'fano_resclas': fano_resclas
            }

            try:
                print(f"Descargando '{filename}'...")
                
                # 6. Realizar la solicitud POST para obtener el archivo.
                response = requests.post(POST_URL, data=payload, timeout=30)
                
                # 7. Verificar si la respuesta es exitosa y guardar el archivo.
                if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Descarga completa: {filename}")
                else:
                    print(f"❌ Error al descargar {filename}. Estado: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"❌ Ocurrió un error de red al intentar descargar {filename}: {e}")

    print("\nProceso finalizado.")


if __name__ == "__main__":
    descargar_resoluciones()