This website is inspired by the AI_Flutter_Project repository which contains the code for a flutter mobile application. While the app is focused on easy inputs and a clear list view, the website's design allows for more information to be displayed to the user at a glance.

Link: https://coffeevueproject.47nj8h7gzj.workers.dev

This is a full stack web application that utilizes multiple platforms.

# 1. Business Case
This website is designed to provide data analytics and generative AI to potential or existing coffee shop owners. This project can help shop owners who want a idea of how much it cost to run a coffee shop. Or existing owners / managers who want to know the effect certain variables will have on the bottom line. Café aux Données is a unique and easy way to keep track of important data when running a coffee shop. 

# 2. Front-end
The designs for the frontend development were conceptualized using Figma. At the heart of my designs, I wanted the website to be easy to use and to add as much customization as possible. If the default theme is too bright for the user, there's a separate, dark mode theme for more customization.

The app is coded using Vue.js front-end JavaScript framework and tested on 13" and 14" laptops and a 27" monitor. Many UI components were constructed using the PrimeVue library.

# 3. Hosting
The website is hosted using CloudFlare. Once the user enters the website, if they are logged in, they'll be presented with the home page. If they are not logged in, they are routed to the log in page.

# 4. Database
The user's information is stored in Firebase. On registration, the user is presented with demo data, but once they add their first entry, the only information displayed is that that is stored in their account. 

# 5. API Requests
I use a Rest API over https to send the user's information to an Ubuntu server. The server is an EC2 virtual server through AWS. A domain name with a valid certificate communicates with the app and routes traffic to the server's ip address. Nginx and Flask API take the information and run a python script to pass the data through a linear regression model.

# 6. Linear Regression Model
The model has 2 linear layers with a Mish activation function in between. More details can be found in the AI_Flutter_Project repository
