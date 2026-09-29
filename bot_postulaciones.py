import json
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from playwright.sync_api import sync_playwright

# Cargar perfil maestro
with open("perfil.json", "r", encoding="utf-8") as f:
    perfil = json.load(f)

def generar_respuesta_motivacion(nombre_empresa, titulo_puesto):
    return (
        f"Hola. Me entusiasma mucho la propuesta de {nombre_empresa} para el puesto de {titulo_puesto}. "
        f"Como estudiante de {perfil['educacion']['carrera']} en la {perfil['educacion']['universidad']} "
        f"({perfil['educacion']['estado']}), busco aportar mi experiencia práctica en optimización de procesos, "
        f"manejo de herramientas analíticas como Power BI y Excel avanzado, y mi enfoque orientado a la mejora continua."
    )

def enviar_reporte_email(posts_realizados):
    remitente = "santilupi1@gmail.com"
    destinatario = "santilupi1@gmail.com"
    password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not password:
        print("⚠️ Advertencia: No se encontró la variable de entorno GMAIL_APP_PASSWORD. Omitiendo envío de correo.")
        return

    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = f"📊 Reporte Diario de Postulaciones - {datetime.now().strftime('%Y-%m-%d')}"

    cuerpo = "Hola Santiago,\n\nAquí tienes el resumen de las postulaciones realizadas automáticamente hoy:\n\n"
    if posts_realizados:
        for p in posts_realizados:
            cuerpo += f"• Empresa: {p['Empresa']}\n  Puesto: {p['Puesto']}\n  Plataforma: {p['Plataforma']}\n  Estado: {p['Estado']}\n\n"
    else:
        cuerpo += "No se registraron nuevas postulaciones el día de hoy.\n"

    cuerpo += "¡Que tengas un excelente día!\nBot Automatizado de Empleo"
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        print("📧 Reporte diario enviado con éxito por mail.")
    except Exception as e:
        print(f"⚠️ Error al enviar el correo: {e}")

def simular_comportamiento_humano(page):
    page.wait_for_timeout(random.randint(2000, 4500))

def run_bot():
    user_data_dir = os.path.expanduser("~/.bot_browser_profile")
    keywords = perfil["rol_buscado"]
    postulaciones_hoy = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=os.environ.get("BOT_HEADLESS", "0") == "1",
            slow_mo=80,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page()
        print("--- INICIANDO AUTOMATIZACIÓN DE EMPLEOS ---")

        for kw in keywords[:3]:
            try:
                print(f"\nBuscando ofertas para: '{kw}'...")
                query_url = f"https://www.linkedin.com/jobs/search/?keywords={kw.replace(' ', '%20')}&location=Argentina"
                page.goto(query_url)
                page.wait_for_timeout(6000)

                ofertas = page.locator(".jobs-search-results-list__list-item, li.occludable-update").all()[:2]

                for oferta in ofertas:
                    try:
                        oferta.scroll_into_view_if_needed()
                        oferta.click()
                        simular_comportamiento_humano(page)

                        titulo = "Puesto General"
                        for sel in [".job-details-jobs-unified-top-card__job-title", "h1.top-card-layout__title", "h2"]:
                            elem = page.locator(sel)
                            if elem.count() > 0:
                                titulo = elem.first.inner_text().strip()
                                break

                        empresa = "Empresa"
                        for sel in [".job-details-jobs-unified-top-card__company-name", ".topcard__org-name-link", ".job-card-container__company-name"]:
                            elem = page.locator(sel)
                            if elem.count() > 0:
                                empresa = elem.first.inner_text().strip()
                                break

                        easy_apply_btn = page.locator("button.jobs-apply-button, button:has-text('Solicitud sencilla')")

                        if easy_apply_btn.count() > 0:
                            print(f"-> Aplicando vía Easy Apply a: {titulo} en {empresa}")
                            easy_apply_btn.first.click()
                            page.wait_for_timeout(2000)

                            intentos_modal = 0
                            while intentos_modal < 5:
                                next_btn = page.locator("button[aria-label='Continuar al siguiente paso'], button[aria-label='Enviar solicitud'], button:has-text('Siguiente'), button:has-text('Enviar')")
                                if next_btn.count() > 0:
                                    next_btn.first.click()
                                    page.wait_for_timeout(2000)
                                    intentos_modal += 1
                                else:
                                    break

                            close_btn = page.locator("button[aria-label='Cerrar'], button.artdeco-modal__dismiss")
                            if close_btn.count() > 0:
                                close_btn.first.click()

                            estado = "Postulado con éxito (Easy Apply)"
                        else:
                            print(f"-> Oferta externa detectada: {titulo} en {empresa}.")
                            estado = "Detectado / Redirigido a externo"

                        postulaciones_hoy.append({
                            "Empresa": empresa,
                            "Puesto": titulo,
                            "Plataforma": "LinkedIn",
                            "Estado": estado
                        })

                    except Exception as inner_e:
                        print(f"⚠️ Error menor procesando oferta: {inner_e}")

            except Exception as e:
                print(f"⚠️ Error en keyword '{kw}': {e}")

        browser.close()

    enviar_reporte_email(postulaciones_hoy)
    print("--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    run_bot()
