# API Tarjetas de Compras

Creacion de una API Rest con FASTAPI para tarjetas de Compras 
Se quiere poder utilizar esta API para el pago en un sistemas de tarjetas de compras
desde una App Movil con lecturas de QR 

## 🧾 ¿Qué es la API_TARJETA?

La **API_TARJETA** es un servicio web desarrollado para brindar acceso seguro y estructurado a la información de socios, préstamos (ayudas), cuotas y tarjetas emitidas por una entidad mutual o financiera.

Permite integrar estos datos con otras aplicaciones móviles, sistemas de gestión o plataformas web, optimizando consultas y automatizando procesos que antes se realizaban de forma manual.

---

## 🎯 Objetivo de la API

El objetivo principal es ofrecer una forma rápida, confiable y segura de consultar la información operativa de las tarjetas mutuales, sin necesidad de acceder directamente a la base de datos interna de la entidad.

Con esta API se pueden desarrollar aplicaciones móviles, paneles web o integraciones que faciliten la operatoria diaria con socios y comercios.

---

## 👥 ¿Quién puede utilizar esta API?

Esta API está orientada a:

- **Desarrolladores** que integran sistemas con la base de datos de la mutual.
- **Personal administrativo o técnico** que necesita acceder a datos de manera automatizada.
- **Aplicaciones móviles** utilizadas por los socios o empleados de la entidad.
- **Sistemas de terceros**, como Home Banking o apps de beneficios.

El acceso está restringido a usuarios y sistemas autorizados. No es pública.

---

## 🔍 ¿Qué consultas puedo hacer?

A través de distintos endpoints, se puede acceder a:

### 1. 🔐 **Consulta de Socios**
- Buscar un socio por su número de CUIT.
- Obtener su información básica (nombre, tarjeta, estado, etc.).

### 2. 💳 **Consulta de Ayudas / Préstamos**
- Listar las ayudas otorgadas a un socio.
- Consultar una ayuda específica por su número o por código de socio.
- Ver detalles como importe otorgado, fechas, estado y condiciones.

### 3. 🧾 **Consulta de Cuotas**
- Obtener todas las cuotas asociadas a una ayuda específica.
- Ver su estado: pagada o pendiente.
- Ver vencimientos, importes, y fechas de pago.

---

## 📲 Ejemplos de uso comunes

- **Una App de Socios** puede mostrar las ayudas activas y sus cuotas pendientes.
- **Un sistema de la mutual** puede verificar si un socio tiene deudas antes de autorizar una nueva compra.
- **Un panel administrativo** puede listar todos los movimientos financieros de un socio para atención personalizada.

---

## 🔐 Seguridad y Acceso

El acceso a la API está protegido. Para utilizarla es necesario:

- Contar con credenciales de acceso (token o usuario y contraseña).
- Estar autorizado por la entidad administradora.

**No compartas tus credenciales con terceros.**

---

## 📘 Documentación Técnica

La documentación técnica (endpoints, parámetros, formatos de respuesta, errores comunes, etc.) está disponible para desarrolladores.  
Solicitá acceso escribiendo a: [mario@maasoft.com.ar](mailto:mario@maasoft.com.ar)

---

## 📞 Contacto

Si tenés dudas, problemas o querés comenzar a utilizar la API, podés comunicarte con:

**Mario Andrés Ageno**  
**MAASoft – Soluciones en Software**  
📧 Email: [mario@maasoft.com.ar](mailto:mario@maasoft.com.ar)  
🌐 Sitio web: [www.maasoft.com.ar](https://www.maasoft.com.ar)  
📱 Tel / WhatsApp: +54 3498 680413

---

> ⚠️ Esta API es parte del sistema de gestión de tarjetas de una entidad mutual. El uso indebido o no autorizado puede ser penalizado según los términos establecidos.
