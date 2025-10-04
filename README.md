# FYP_PAM
Reducing Security Risks with Privileged Access Management: Real-Time Authentication and User Behavior Analysis using ML

Project Overview

This repository contains the source code, documentation, and resources for the final year project (FYP) thesis titled "Reducing Security Risks with Privileged Access Management: Real-Time Authentication and User Behavior Analysis using ML" by Heshan Rajith. The project was submitted to the Computing School at Staffordshire University in partial fulfillment of the requirements for the Degree of Bachelor of Science in Cyber Security (Hons), supervised by Ms. Ama Jayaweera, in August 2025, Colombo.

Description

This research addresses the limitations of traditional Privileged Access Management (PAM) systems by developing a dynamic PAM system. It integrates real-time OAuth 2.0 authentication with machine learning-based User Behavior Analysis (UBA) to detect anomalies and automate threat responses. The system employs an unsupervised Isolation Forest algorithm for behavioral baseline establishment and real-time anomaly detection.

Key Features

Real-time OAuth 2.0 authentication
Machine learning-based User Behavior Analysis (UBA)
Anomaly detection with a 94.2% success rate
Automated threat response with an average of 2.1 seconds
Flask-based web application interface
Python-based ML engine

Installation

Clone the repository: git clone https://github.com/hesh25/FYP_PAM.git
Navigate to the project directory: cd FYP_Thesis_PAM
Install dependencies: pip install -r requirements.txt
Run the application: python app.py with watcher.py to send the logs

Usage

Access the web interface at http://localhost:5000
Authenticate using OAuth 2.0 credentials
Monitor real-time behavior analysis and alerts

Files and Structure

/src: Contains source code (Flask app, ML models, etc.)
/docs: Includes thesis report (FYP_Thesis_Report_CB011557.pdf) and additional documentation
/tests: Unit and integration test scripts
requirements.txt: List of Python dependencies
README.md: This file

Contributing
Contributions are welcome. Please fork the repository and submit pull requests for review.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments
Ms. Ama Jayaweera for supervision and guidance
115 IT professionals for requirements validation survey
Staffordshire University UK
APIIT LK

Contact

For any questions, please contact Heshan Rajith at rajithheshan12@gmail.com.

Tool Demonstration Video
Watch the Demo - https://youtu.be/V871sijW-W0?si=RcJKiowGZaIegLCC
