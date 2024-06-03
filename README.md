# Basketball Performance Analysis

## Introduction
This project involves a comprehensive analysis of basketball performance data to explore the effects of load management on key performance metrics such as points scored (PTS), assists (AST), rebounds (TRB), and field goal percentage (FG%). The analysis is conducted using statistical methods and Bayesian inference, presented through a Jupyter Notebook.

## Installation

### Prerequisites
Before starting, ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/downloads/). This project requires Python 3.x.

### Setup
1. **Download the Notebook**: Save the `Project.ipynb` file to your computer.
2. **Create a Directory**: Organize your workspace by creating a new directory for the project files.
3. **Create a Virtual Environment** (Optional but recommended):
   - Open your terminal or command prompt.
   - Navigate to the project directory.
   - Run the following command to create a virtual environment:
     ```bash
     python -m venv myenv
     ```
   - Activate the environment:
     - Windows:
       ```bash
       .\myenv\Scripts\activate
       ```
     - MacOS/Linux:
       ```bash
       source myenv/bin/activate
       ```

4. **Install Required Libraries**:
   - Ensure the following content is in your `requirements.txt` file:
     ```
     pandas
     numpy
     matplotlib
     seaborn
     scipy
     statsmodels
     pymc3
     ```
   - Install the libraries by running:
     ```bash
     pip install -r requirements.txt
     ```

### Running the Notebook
Once the environment is set up and dependencies are installed:
- Launch Jupyter Notebook by running:
  ```bash
  jupyter notebook


### Running the Test
- Launch the Test  
  ```bash
  python test_analysis.py


- In the Jupyter Notebook interface, navigate to the project directory and open Project.ipynb to access the notebook.
### Notebook Structure
The notebook includes various sections, each dedicated to different stages of data analysis, from initial preparation and cleaning to complex statistical evaluations:

- Data Preparation: This section involves loading the data into the environment and performing initial data cleaning processes to prepare for analysis.
- Exploratory Data Analysis (EDA): In this part, the data is visualized through various graphs and plots to understand distributions and underlying relationships between variables.
- Statistical Testing: This involves applying statistical tests to evaluate hypotheses and ascertain relationships between different performance metrics.
- Bayesian Inference: This advanced statistical approach is used to perform Bayesian analysis, allowing for a probabilistic interpretation of the data and the estimation of posterior distributions based on prior knowledge and the likelihood of observed data.
