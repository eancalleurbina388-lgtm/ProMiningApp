import json
import os
import re
import urllib.parse
import urllib.request
import difflib
from html import unescape

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivy.uix.scrollview import ScrollView

# Base de datos local rápida (Soporta búsqueda instantánea sin internet)
BD_MINERALES = {
    "galena": {
        "nombre": "Galena",
        "formula": "PbS",
        "composicion": "Pb: 86.60% | S: 13.40%",
        "sistema": "Cúbico / Isométrico",
        "habito": "Cúbico, octaédrico, masivo, granular",
        "dureza": "2.5 (Mohs)",
        "densidad": "7.50 - 7.60 t/m³",
        "brillo": "Metálico intenso",
        "color": "Gris plomo",
        "raya": "Gris plomo oscura",
        "exfoliacion": "Perfecta cúbica {100}",
        "fractura": "Subconcoidea a desigual",
        "tenacidad": "Frágil",
        "genesis": "Hidrotermal de media a baja temperatura en vetas y reemplazamiento en carbonatos (Skarn / MVT).",
        "paragenesis": "Esfalerita, Calcopirita, Pirita, Marcasita, Baritina, Calcita, Cuarzo."
    },
    "pirita": {
        "nombre": "Pirita",
        "formula": "FeS2",
        "composicion": "Fe: 46.55% | S: 53.45%",
        "sistema": "Cúbico / Isométrico",
        "habito": "Cúbico estriado, piritoédrico, masivo, granular",
        "dureza": "6.0 - 6.5 (Mohs)",
        "densidad": "5.00 - 5.10 t/m³",
        "brillo": "Metálico brillante",
        "color": "Amarillo latón pálido",
        "raya": "Negra verdosa a negra parduzca",
        "exfoliacion": "Imperfecta / Muy débil {001}",
        "fractura": "Concoidea a desigual",
        "tenacidad": "Frágil",
        "genesis": "Magmática, sedimentaria, metamórfica e hidrotermal (vulkanogénico / pórfidos).",
        "paragenesis": "Calcopirita, Galena, Esfalerita, Cuarzo, Calcita, Oro nativo."
    },
    "calcopirita": {
        "nombre": "Calcopirita",
        "formula": "CuFeS2",
        "composicion": "Cu: 34.63% | Fe: 30.43% | S: 34.94%",
        "sistema": "Tetragonal",
        "habito": "Escalenoédrico, tetraédrico, masivo, botroidal",
        "dureza": "3.5 - 4.0 (Mohs)",
        "densidad": "4.10 - 4.30 t/m³",
        "brillo": "Metálico",
        "color": "Amarillo latón con pátinas iridiscentes",
        "raya": "Negra verdosa",
        "exfoliacion": "Poco clara {011}",
        "fractura": "Desigual",
        "tenacidad": "Frágil",
        "genesis": "Hidrotermal en depósitos pórfidos de Cu, vetas, skarns y sulfuros masivos (VMS).",
        "paragenesis": "Pirita, Esfalerita, Galena, Bornita, Magnetita, Cuarzo, Calcita."
    }
}

class Tab(MDFloatLayout, MDTabsBase):
    pass

class CalculadoraMineraApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Amber"
        self.theme_cls.accent_palette = "BlueGray"
        self.theme_cls.theme_style = "Dark"
        
        if os.path.exists("icon.png"):
            self.icon = "icon.png"

        screen = MDScreen()
        main_layout = MDBoxLayout(orientation="vertical")

        titulo = MDLabel(
            text="PRO-MINING TOOLS",
            halign="center",
            font_style="H5",
            theme_text_color="Primary",
            size_hint_y=None,
            height=50
        )
        main_layout.add_widget(titulo)

        tabs = MDTabs()

        # --- PESTAÑA 1: TONELAJE ---
        tab1 = Tab(title="Tonelaje")
        layout_tab1 = MDBoxLayout(orientation="vertical", spacing=10, padding=15)
        
        inputs_box1 = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        inputs_box1.bind(minimum_height=inputs_box1.setter('height'))
        
        self.input_volumen = MDTextField(hint_text="Volumen de material V (m³)", input_filter="float", mode="rectangle")
        self.input_densidad = MDTextField(hint_text="Densidad del mineral ρ (t/m³)", input_filter="float", mode="rectangle")
        btn_calc_ton = MDRaisedButton(text="CALCULAR TONELAJE (PASO A PASO)", pos_hint={"center_x": 0.5}, on_release=self.calcular_tonelaje)
        
        inputs_box1.add_widget(self.input_volumen)
        inputs_box1.add_widget(self.input_densidad)
        inputs_box1.add_widget(btn_calc_ton)

        scroll_ton = ScrollView(size_hint=(1, 1))
        self.lbl_res_ton = MDLabel(
            text="[color=#FFC107]Ingrese los datos para desplegar el desarrollo paso a paso.[/color]",
            markup=True,
            halign="left",
            font_style="Body1",
            size_hint_y=None
        )
        self.lbl_res_ton.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_ton.add_widget(self.lbl_res_ton)

        layout_tab1.add_widget(inputs_box1)
        layout_tab1.add_widget(scroll_ton)
        tab1.add_widget(layout_tab1)

        # --- PESTAÑA 2: LEYES (Au/Ag) ---
        tab2 = Tab(title="Leyes (Au/Ag)")
        layout_tab2 = MDBoxLayout(orientation="vertical", spacing=10, padding=15)
        
        inputs_box2 = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        inputs_box2.bind(minimum_height=inputs_box2.setter('height'))

        self.input_ley_gt = MDTextField(hint_text="Ley en gramos por tonelada (g/t)", input_filter="float", mode="rectangle")
        btn_calc_ley = MDRaisedButton(text="CONVERTIR A OZ/T (PASO A PASO)", pos_hint={"center_x": 0.5}, on_release=self.convertir_ley)
        
        inputs_box2.add_widget(self.input_ley_gt)
        inputs_box2.add_widget(btn_calc_ley)

        scroll_ley = ScrollView(size_hint=(1, 1))
        self.lbl_res_ley = MDLabel(
            text="[color=#FFC107]Ingrese la ley en g/t para desplegar la conversión paso a paso.[/color]",
            markup=True,
            halign="left",
            font_style="Body1",
            size_hint_y=None
        )
        self.lbl_res_ley.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_ley.add_widget(self.lbl_res_ley)

        layout_tab2.add_widget(inputs_box2)
        layout_tab2.add_widget(scroll_ley)
        tab2.add_widget(layout_tab2)

        # --- PESTAÑA 3: RQD GEOMECÁNICA ---
        tab3 = Tab(title="RQD Geomecánica")
        layout_tab3 = MDBoxLayout(orientation="vertical", spacing=10, padding=15)

        inputs_box3 = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        inputs_box3.bind(minimum_height=inputs_box3.setter('height'))

        self.input_trozos = MDTextField(hint_text="Suma de trozos ≥ 10 cm (m o cm)", input_filter="float", mode="rectangle")
        self.input_longitud_total = MDTextField(hint_text="Longitud total corrida del testigo (m o cm)", input_filter="float", mode="rectangle")
        btn_calc_rqd = MDRaisedButton(text="CALCULAR RQD (PASO A PASO)", pos_hint={"center_x": 0.5}, on_release=self.calcular_rqd)

        inputs_box3.add_widget(self.input_trozos)
        inputs_box3.add_widget(self.input_longitud_total)
        inputs_box3.add_widget(btn_calc_rqd)

        scroll_rqd = ScrollView(size_hint=(1, 1))
        self.lbl_res_rqd = MDLabel(
            text="[color=#FFC107]Ingrese los datos del testigo para desplegar el cálculo paso a paso.[/color]",
            markup=True,
            halign="left",
            font_style="Body1",
            size_hint_y=None
        )
        self.lbl_res_rqd.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_rqd.add_widget(self.lbl_res_rqd)

        layout_tab3.add_widget(inputs_box3)
        layout_tab3.add_widget(scroll_rqd)
        tab3.add_widget(layout_tab3)

        # --- PESTAÑA 4: MINERALOGÍA UNIVERSAL ---
        tab4 = Tab(title="Mineralogía")
        layout_tab4 = MDBoxLayout(orientation="vertical", spacing=10, padding=15)

        inputs_box4 = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        inputs_box4.bind(minimum_height=inputs_box4.setter('height'))

        self.input_mineral = MDTextField(
            hint_text="Escribe CUALQUIER mineral (ej: Skutterudita, Enargita, Realgar...)",
            mode="rectangle"
        )
        btn_buscar_min = MDRaisedButton(
            text="BUSCAR Y EXTRAER PROPIEDADES",
            pos_hint={"center_x": 0.5},
            on_release=self.buscar_mineral
        )

        inputs_box4.add_widget(self.input_mineral)
        inputs_box4.add_widget(btn_buscar_min)

        scroll_min = ScrollView(size_hint=(1, 1))
        self.lbl_res_mineral = MDLabel(
            text="[color=#FFC107]Ingresa el nombre de CUALQUIER mineral del mundo para extraer sus propiedades geológicas.[/color]",
            markup=True,
            halign="left",
            font_style="Body1",
            size_hint_y=None
        )
        self.lbl_res_mineral.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_min.add_widget(self.lbl_res_mineral)

        layout_tab4.add_widget(inputs_box4)
        layout_tab4.add_widget(scroll_min)
        tab4.add_widget(layout_tab4)

        # --- PESTAÑA 5: DRENAJE ÁCIDO DE MINA (DAM) ---
        tab5 = Tab(title="Módulo DAM")
        layout_tab5 = MDBoxLayout(orientation="vertical", spacing=10, padding=15)

        inputs_box5 = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        inputs_box5.bind(minimum_height=inputs_box5.setter('height'))

        self.input_azufre = MDTextField(hint_text="Porcentaje de Azufre Total S (%)", input_filter="float", mode="rectangle")
        self.input_np = MDTextField(hint_text="Potencial de Neutralización NP (kg CaCO₃/t)", input_filter="float", mode="rectangle")
        btn_calc_dam = MDRaisedButton(text="EVALUAR POTENCIAL DAM (PASO A PASO)", pos_hint={"center_x": 0.5}, on_release=self.calcular_dam)

        inputs_box5.add_widget(self.input_azufre)
        inputs_box5.add_widget(self.input_np)
        inputs_box5.add_widget(btn_calc_dam)

        scroll_dam = ScrollView(size_hint=(1, 1))
        self.lbl_res_dam = MDLabel(
            text="[color=#FFC107]Ingrese el % de Azufre y el NP para evaluar el potencial de Drenaje Ácido de Mina (DAM).[/color]",
            markup=True,
            halign="left",
            font_style="Body1",
            size_hint_y=None
        )
        self.lbl_res_dam.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_dam.add_widget(self.lbl_res_dam)

        layout_tab5.add_widget(inputs_box5)
        layout_tab5.add_widget(scroll_dam)
        tab5.add_widget(layout_tab5)

        tabs.add_widget(tab1)
        tabs.add_widget(tab2)
        tabs.add_widget(tab3)
        tabs.add_widget(tab4)
        tabs.add_widget(tab5)

        main_layout.add_widget(tabs)
        screen.add_widget(main_layout)
        return screen

    # -------------------------------------------------------------------------
    # DESARROLLOS MATEMÁTICOS Y AMBIENTALES
    # -------------------------------------------------------------------------
    
    def calcular_tonelaje(self, instance):
        try:
            vol = float(self.input_volumen.text)
            den = float(self.input_densidad.text)
            ton = vol * den

            pasos = (
                f"[size=18][b][color=#FFC107]DESARROLLO PASO A PASO: TONELAJE[/color][/b][/size]\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"[b]PASO 1: DATOS DE ENTRADA[/b]\n"
                f"   • Volumen (V) = [color=#00E676]{vol:,.2f} m³[/color]\n"
                f"   • Densidad (ρ) = [color=#00E676]{den:,.2f} t/m³[/color]\n\n"
                f"[b]PASO 2: ANÁLISIS DIMENSIONAL DE UNIDADES[/b]\n"
                f"   • [color=#00E676][m³] × [t / m³] = [t][/color]\n\n"
                f"[b]PASO 3: FÓRMULA DE TONELAJE[/b]\n"
                f"   • [color=#FFB74D]T = V × ρ[/color]\n\n"
                f"[b]PASO 4: SUSTITUCIÓN DE VALORES[/b]\n"
                f"   • [color=#FFB74D]T = {vol:,.2f} m³ × {den:,.2f} t/m³[/color]\n\n"
                f"[b]PASO 5: RESULTADO FINAL[/b]\n"
                f"   • [color=#00E676][b]T = {ton:,.2f} Toneladas (t)[/b][/color]"
            )
            self.lbl_res_ton.text = pasos
        except ValueError:
            self.lbl_res_ton.text = "[color=#FF5252]⚠️ Error: Ingrese valores numéricos válidos en ambos campos.[/color]"

    def convertir_ley(self, instance):
        try:
            gt = float(self.input_ley_gt.text)
            factor = 31.1034768
            ozt = gt / factor

            pasos = (
                f"[size=18][b][color=#FFC107]DESARROLLO PASO A PASO: CONVERSIÓN DE LEYES[/color][/b][/size]\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"[b]PASO 1: DATOS DE ENTRADA Y FACTOR DE CONVERSIÓN[/b]\n"
                f"   • Ley ingresada = [color=#00E676]{gt:,.4f} g/t[/color]\n"
                f"   • Equivalencia troy = [color=#00E676]1 oz troy = 31.1035 g[/color]\n\n"
                f"[b]PASO 2: ANÁLISIS DIMENSIONAL DE UNIDADES[/b]\n"
                f"   • [color=#00E676][g/t] ÷ [g / oz troy] = [oz troy / t][/color]\n\n"
                f"[b]PASO 3: FÓRMULA DE CONVERSIÓN[/b]\n"
                f"   • [color=#FFB74D]Ley (oz/t) = Ley (g/t) ÷ 31.1034768[/color]\n\n"
                f"[b]PASO 4: SUSTITUCIÓN DE VALORES[/b]\n"
                f"   • [color=#FFB74D]Ley (oz/t) = {gt:,.4f} g/t ÷ 31.1034768 g/oz[/color]\n\n"
                f"[b]PASO 5: RESULTADO FINAL[/b]\n"
                f"   • [color=#00E676][b]Ley = {ozt:,.4f} oz/t (Onzas Troy por Tonelada)[/b][/color]"
            )
            self.lbl_res_ley.text = pasos
        except ValueError:
            self.lbl_res_ley.text = "[color=#FF5252]⚠️ Error: Ingrese un valor numérico válido.[/color]"

    def calcular_rqd(self, instance):
        try:
            trozos = float(self.input_trozos.text)
            total = float(self.input_longitud_total.text)

            if total <= 0:
                self.lbl_res_rqd.text = "[color=#FF5252]⚠️ Error: La longitud total debe ser mayor a 0.[/color]"
                return

            if trozos > total:
                self.lbl_res_rqd.text = "[color=#FF5252]⚠️ Error: La suma de trozos no puede ser mayor que la longitud total.[/color]"
                return

            rqd = (trozos / total) * 100
            calidad = "Muy Mala" if rqd < 25 else "Mala" if rqd < 50 else "Regular" if rqd < 75 else "Buena" if rqd < 90 else "Excelente"

            pasos = (
                f"[size=18][b][color=#FFC107]DESARROLLO PASO A PASO: EVALUACIÓN RQD[/color][/b][/size]\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"[b]PASO 1: DATOS DE CAMPO DE ROCA[/b]\n"
                f"   • Suma de trozos intactos (≥ 10 cm) = [color=#00E676]{trozos:,.2f}[/color]\n"
                f"   • Longitud total perfo / corrida = [color=#00E676]{total:,.2f}[/color]\n\n"
                f"[b]PASO 2: FÓRMULA GEOMECÁNICA (DEERE ET AL.)[/b]\n"
                f"   • [color=#FFB74D]RQD (%) = ( Suma de trozos ≥ 10 cm ÷ Longitud Total ) × 100%[/color]\n\n"
                f"[b]PASO 3: SUSTITUCIÓN Y CÁLCULO[/b]\n"
                f"   • [color=#FFB74D]RQD (%) = ( {trozos:,.2f} ÷ {total:,.2f} ) × 100%[/color]\n"
                f"   • [color=#FFB74D]RQD (%) = {trozos / total:.4f} × 100%[/color]\n\n"
                f"[b]PASO 4: RESULTADO E INTERPRETACIÓN GEOMECÁNICA[/b]\n"
                f"   • [color=#00E676][b]RQD = {rqd:.1f}%[/b][/color]\n"
                f"   • Calidad de Matriz Rocosa: [color=#00E676][b]{calidad.upper()}[/b][/color]"
            )
            self.lbl_res_rqd.text = pasos
        except ValueError:
            self.lbl_res_rqd.text = "[color=#FF5252]⚠️ Error: Ingrese valores numéricos válidos en ambos campos.[/color]"

    def calcular_dam(self, instance):
        try:
            s_pct = float(self.input_azufre.text)
            np_val = float(self.input_np.text)

            # Método Sobek et al. (1978)
            ap_val = s_pct * 31.25
            nnp = np_val - ap_val
            ratio = (np_val / ap_val) if ap_val > 0 else 999.0

            if ratio < 1.0 or nnp < -20:
                clasificacion = "Potencialmente Generador de Ácido (PAG)"
            elif ratio > 3.0 or nnp > 20:
                clasificacion = "No Generador de Ácido (NAG)"
            else:
                clasificacion = "Incierto (Requiere pruebas cinéticas)"

            pasos = (
                f"[size=18][b][color=#FFC107]DESARROLLO PASO A PASO: EVALUACIÓN DAM (Sobek)[/color][/b][/size]\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"[b]PASO 1: DATOS DE LABORATORIO[/b]\n"
                f"   • Azufre Total (S%) = [color=#00E676]{s_pct:,.2f} %[/color]\n"
                f"   • Potencial de Neutralización (NP) = [color=#00E676]{np_val:,.2f} kg CaCO₃/t[/color]\n\n"
                f"[b]PASO 2: CÁLCULO DEL POTENCIAL DE ACIDEZ (AP)[/b]\n"
                f"   • [color=#FFB74D]AP = %S × 31.25[/color]\n"
                f"   • [color=#FFB74D]AP = {s_pct:,.2f} × 31.25 = {ap_val:,.2f} kg CaCO₃/t[/color]\n\n"
                f"[b]PASO 3: CÁLCULO DEL POTENCIAL NETO DE NEUTRALIZACIÓN (NNP)[/b]\n"
                f"   • [color=#FFB74D]NNP = NP - AP[/color]\n"
                f"   • [color=#FFB74D]NNP = {np_val:,.2f} - {ap_val:,.2f} = {nnp:,.2f} kg CaCO₃/t[/color]\n\n"
                f"[b]PASO 4: RELACIÓN NP / AP[/b]\n"
                f"   • [color=#FFB74D]Ratio = NP ÷ AP = {np_val:,.2f} ÷ {ap_val:,.2f} = {ratio:.2f}[/color]\n\n"
                f"[b]PASO 5: CLASIFICACIÓN AMBIENTAL[/b]\n"
                f"   • [color=#00E676][b]{clasificacion}[/b][/color]"
            )
            self.lbl_res_dam.text = pasos
        except ValueError:
            self.lbl_res_dam.text = "[color=#FF5252]⚠️ Error: Ingrese valores numéricos válidos en ambos campos.[/color]"

    # -------------------------------------------------------------------------
    # MINERALOGÍA UNIVERSAL CON PARSER AUTOMÁTICO DE INFOPAGES WEB
    # -------------------------------------------------------------------------

    def renderizar_ficha(self, data, es_remoto=False):
        aviso = " [i][color=#90A4AE](Extraído automáticamente de la red)[/color][/i]" if es_remoto else ""
        
        texto = (
            f"[size=20][b][color=#FFC107]MINERAL: {data['nombre'].upper()}[/color][/b][/size]{aviso}\n\n"
            f"[size=16][b][color=#FFB74D]1. FÓRMULA Y COMPOSICIÓN QUÍMICA[/color][/b][/size]\n"
            f"• [b]Fórmula Química:[/b] {data.get('formula', 'Ver descripción')}\n"
            f"• [b]Composición Elemental (%):[/b] {data.get('composicion', 'Variable según ambiente de formación')}\n\n"
            f"[size=16][b][color=#00E676]2. PROPIEDADES FÍSICAS Y CRISTALINAS[/color][/b][/size]\n"
            f"• [b]Sistema Cristalino:[/b] {data.get('sistema', 'No especificado')}\n"
            f"• [b]Hábito Cristalino:[/b] {data.get('habito', 'No especificado')}\n"
            f"• [b]Dureza (Escala Mohs):[/b] {data.get('dureza', 'No especificado')}\n"
            f"• [b]Densidad / P.E.:[/b] {data.get('densidad', 'No especificado')}\n"
            f"• [b]Brillo / Lustre:[/b] {data.get('brillo', 'No especificado')}\n"
            f"• [b]Color:[/b] {data.get('color', 'No especificado')}\n"
            f"• [b]Raya / Huella:[/b] {data.get('raya', 'No especificado')}\n"
            f"• [b]Exfoliación / Clivaje:[/b] {data.get('exfoliacion', 'No especificada')}\n"
            f"• [b]Fractura:[/b] {data.get('fractura', 'No especificada')}\n"
            f"• [b]Tenacidad / Cohesión:[/b] {data.get('tenacidad', 'No especificada')}\n\n"
            f"[size=16][b][color=#29B6F6]3. GÉNESIS GEOLÓGICA & AMBIENTE[/color][/b][/size]\n"
            f"{data.get('genesis', 'No disponible')}\n\n"
            f"[size=16][b][color=#AB47BC]4. PARAGÉNESIS (MINERALES ASOCIADOS)[/color][/b][/size]\n"
            f"{data.get('paragenesis', 'Asociado comúnmente en vetas e hidrotermalismo')}"
        )
        self.lbl_res_mineral.text = texto

    def buscar_en_red_global_parser(self, query_raw):
        try:
            url_encoded = urllib.parse.quote(query_raw)
            wiki_html_url = f"https://es.wikipedia.org/wiki/{url_encoded}"
            
            req = urllib.request.Request(
                wiki_html_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    return False
                html_bytes = response.read()
                html_text = html_bytes.decode('utf-8', errors='ignore')

            def limpiar_html(raw_html):
                cleanr = re.compile('<.*?>')
                text = re.sub(cleanr, '', raw_html)
                text = unescape(text)
                return text.strip().replace('\n', ' ')

            parsed_data = {
                "nombre": query_raw.capitalize(),
                "formula": "No detectada",
                "composicion": "Consultar análisis químico instrumental (ICP-MS)",
                "sistema": "No especificado",
                "habito": "Prismático, masivo o granular",
                "dureza": "No especificado",
                "densidad": "No especificado",
                "brillo": "Metálico / Submetálico / Vítreo",
                "color": "Variable",
                "raya": "No especificado",
                "exfoliacion": "No especificada",
                "fractura": "Desigual",
                "tenacidad": "Frágil",
                "genesis": "Ambiente de formación geológica e hidrotermal.",
                "paragenesis": "Sulfuros y gangas asociadas."
            }

            tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', html_text, re.DOTALL | re.IGNORECASE)
            
            for tr in tr_blocks:
                if '<th' in tr.lower() and '<td' in tr.lower():
                    th_match = re.search(r'<th[^>]*>(.*?)</th>', tr, re.DOTALL | re.IGNORECASE)
                    td_match = re.search(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
                    
                    if th_match and td_match:
                        header = limpiar_html(th_match.group(1)).lower()
                        val = limpiar_html(td_match.group(1))

                        if "fórmula" in header:
                            parsed_data["formula"] = val
                        elif "sistema" in header:
                            parsed_data["sistema"] = val
                        elif "hábito" in header:
                            parsed_data["habito"] = val
                        elif "dureza" in header:
                            parsed_data["dureza"] = val + " (Mohs)" if "Mohs" not in val else val
                        elif "densidad" in header or "peso específico" in header:
                            parsed_data["densidad"] = val
                        elif "brillo" in header or "lustre" in header:
                            parsed_data["brillo"] = val
                        elif "color" in header:
                            parsed_data["color"] = val
                        elif "raya" in header or "huella" in header:
                            parsed_data["raya"] = val
                        elif "exfoliación" in header or "clivaje" in header:
                            parsed_data["exfoliacion"] = val
                        elif "fractura" in header:
                            parsed_data["fractura"] = val
                        elif "tenacidad" in header:
                            parsed_data["tenacidad"] = val

            p_blocks = re.findall(r'<p[^>]*>(.*?)</p>', html_text, re.DOTALL | re.IGNORECASE)
            resumen_parrafos = []
            for p in p_blocks:
                p_clean = limpiar_html(p)
                if len(p_clean) > 40:
                    resumen_parrafos.append(p_clean)
                if len(resumen_parrafos) >= 2:
                    break

            if resumen_parrafos:
                parsed_data["genesis"] = resumen_parrafos[0]
                if len(resumen_parrafos) > 1:
                    parsed_data["paragenesis"] = resumen_parrafos[1]

            self.renderizar_ficha(parsed_data, es_remoto=True)
            return True

        except Exception:
            pass
        return False

    def buscar_mineral(self, instance):
        query_raw = self.input_mineral.text.strip()
        query = query_raw.lower()

        if not query:
            self.lbl_res_mineral.text = "[color=#FF5252]Por favor ingresa el nombre de un mineral.[/color]"
            return

        self.lbl_res_mineral.text = f"[color=#FFC107]Buscando y procesando propiedades de '{query_raw}'...[/color]"

        if query in BD_MINERALES:
            self.renderizar_ficha(BD_MINERALES[query], es_remoto=False)
            return

        if self.buscar_en_red_global_parser(query_raw):
            return

        coincidencias = difflib.get_close_matches(query, BD_MINERALES.keys(), n=1, cutoff=0.7)
        if coincidencias:
            self.renderizar_ficha(BD_MINERALES[coincidencias[0]], es_remoto=False)
            return

        self.lbl_res_mineral.text = f"[color=#FF5252]No se encontró información para '{query_raw}'. Asegúrate de que exista o revisa la conexión.[/color]"

if __name__ == "__main__":
    CalculadoraMineraApp().run()