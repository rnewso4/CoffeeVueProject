# Café aux Données

**Coffee shop analytics and forecasting for owners and managers.**

Live demo: [https://coffeevueproject.47nj8h7gzj.workers.dev](https://coffeevueproject.47nj8h7gzj.workers.dev)

This project is a full-stack web application inspired by the [AI_Flutter_Project](https://github.com) repository. While the original Flutter app emphasizes quick inputs and a simple list view, this web version is designed to surface more information at a glance and support deeper data exploration.

---

## 1. Business case

Café aux Données helps current and prospective coffee shop owners understand costs, margins, and the impact of key variables on profitability. Use it to:

- Estimate what it costs to run a coffee shop.
- Model how changes in inputs (e.g., labor, ingredients, foot traffic) affect the bottom line.
- Track and analyze operational data in one place.

The application combines data analytics with generative AI to make planning and decision-making more informed and accessible.

---

## 2. Front-end

- **Design:** Concepts were developed in Figma with a focus on usability and customization (including an optional dark theme).
- **Stack:** Vue 3, Vite, PrimeVue, Chart.js. Tested on 13" and 14" laptops and 27" monitors.
- **UX:** Clear navigation, responsive layout, and theme options so users can work in a comfortable environment.

---

## 3. Hosting

The application is hosted on **Cloudflare Workers**. Access is gated by authentication: authenticated users see the home dashboard; unauthenticated users are redirected to the login page.

---

## 4. Database

User accounts and application data are stored in **Firebase**. New users receive demo data on registration; after they add their first real entry, only their own account data is shown.

---

## 5. API layer

A **REST API over HTTPS** sends user data to a backend running on an **AWS EC2** (Ubuntu) instance. Traffic is routed via a domain with a valid TLS certificate. **Nginx** and a **Flask** API receive requests and delegate to a Python pipeline that runs the forecasting model.

---

## 6. Forecasting model

The backend uses a **linear regression**-style model with two linear layers and a **Mish** activation function between them. For model details and training setup, see the AI_Flutter_Project repository.

---

## Tech summary

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Front-end  | Vue 3, Vite, PrimeVue, Chart.js     |
| Hosting    | Cloudflare Workers                  |
| Database   | Firebase                            |
| Backend    | Flask on AWS EC2 (Ubuntu), Nginx    |
| ML/Stats   | Custom linear model (Mish activation) |
