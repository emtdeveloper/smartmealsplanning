import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def create_macronutrient_chart(macros):
    """
    Create a pie chart showing macronutrient distribution
    
    Parameters:
    - macros: dict with keys 'protein', 'carbs', 'fat' and their values in grams
    
    Returns:
    - Plotly figure object
    """
    # Calculate calories from each macro
    protein_cals = macros['protein'] * 4
    carb_cals = macros['carbs'] * 4
    fat_cals = macros['fat'] * 9
    
    total_cals = protein_cals + carb_cals + fat_cals
    
    # Calculate percentages
    protein_pct = (protein_cals / total_cals) * 100
    carb_pct = (carb_cals / total_cals) * 100
    fat_pct = (fat_cals / total_cals) * 100
    
    # Create the pie chart
    labels = ['Protein', 'Carbohydrates', 'Fat']
    values = [protein_pct, carb_pct, fat_pct]
    colors = ['#4CAF50', '#2196F3', '#FFC107']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        hoverinfo='label+value',
        textfont=dict(size=14)
    )])
    
    fig.update_layout(
        title='Macronutrient Distribution',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    # Add annotation in the middle
    fig.add_annotation(
        text=f'{int(total_cals)}<br>calories',
        x=0.5, y=0.5,
        font=dict(size=16, color='#fc3d45', family='Arial, sans-serif'),
        showarrow=False
    )
    
    return fig

def create_weight_progress_chart(progress_data):
    """
    Create a line chart showing weight progress over time
    
    Parameters:
    - progress_data: list of dicts with 'timestamp' and 'weight' keys
    
    Returns:
    - Plotly figure object
    """
    if not progress_data:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title='Weight Progress',
            xaxis_title='Date',
            yaxis_title='Weight (kg)',
            height=400
        )
        return fig
    
    # Convert list of dicts to dataframe
    df = pd.DataFrame(progress_data)
    
    # Convert timestamps to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Create the line chart
    fig = px.line(
        df, 
        x='timestamp', 
        y='weight',
        markers=True,
        labels={'timestamp': 'Date', 'weight': 'Weight (kg)'},
        title='Weight Progress'
    )
    
    # Update layout for better appearance
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            tickangle=-45,
            tickformat='%Y-%m-%d',
            tickmode='auto',
            nticks=10
        ),
        yaxis=dict(
            gridcolor='lightgray'
        ),
        plot_bgcolor='white'
    )
    
    # Add trendline
    if len(df) > 1:
        fig.add_traces(
            px.scatter(
                df, 
                x='timestamp', 
                y='weight', 
                trendline='ols'
            ).data[1]
        )
    
    return fig

def create_bmi_chart(bmi, status):
    """
    Create a gauge chart showing BMI and status
    
    Parameters:
    - bmi: BMI value
    - status: Status string (e.g., 'Underweight', 'Healthy', 'Overweight', 'Obese')
    
    Returns:
    - Plotly figure object
    """
    # Define BMI categories and their color codes
    categories = ['Underweight', 'Healthy', 'Overweight', 'Obese']
    colors = ['#90CAF9', '#4CAF50', '#FFC107', '#F44336']
    
    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=bmi,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f'BMI - {status}', 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 40], 'tickwidth': 1, 'tickcolor': 'darkblue'},
            'bar': {'color': 'darkblue'},
            'bgcolor': 'white',
            'borderwidth': 2,
            'bordercolor': 'gray',
            'steps': [
                {'range': [0, 18.5], 'color': colors[0]},
                {'range': [18.5, 25], 'color': colors[1]},
                {'range': [25, 30], 'color': colors[2]},
                {'range': [30, 40], 'color': colors[3]}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': bmi
            }
        }
    ))
    
    # fig.update_layout(
    #     height=300,
    #     margin=dict(l=20, r=20, t=50, b=20),
    #     font={'color': 'darkblue', 'family': 'Arial'}
    # )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        font={'color': 'darkblue', 'family': 'Arial'},
        paper_bgcolor='#F5F5F5',  # Light gray background for the figure
        plot_bgcolor='#F5F5F5',  # Match the plot area
        annotations=[
            dict(
                x=0.5,
                y=-0.1,
                xref="paper",
                yref="paper",
                text="Body Mass Index (BMI)",
                showarrow=False,
                font=dict(size=14, color='darkblue')
            )
        ],
        shapes=[
            # Add a subtle shadow effect around the gauge
            dict(
                type="rect",
                x0=0.05,
                y0=0.05,
                x1=0.95,
                y1=0.95,
                xref="paper",
                yref="paper",
                fillcolor="white",
                opacity=0.8,
                line=dict(color="gray", width=1),
                layer="below"
            )
        ]
    )
    
    return fig

def create_meal_plan_calories_chart(meal_plan):
    """
    Create a bar chart showing daily calories in a meal plan
    
    Parameters:
    - meal_plan: Dict containing meal plan information with 'days' key
    
    Returns:
    - Plotly figure object
    """
    if not meal_plan or 'days' not in meal_plan:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title='Daily Calories',
            xaxis_title='Day',
            yaxis_title='Calories',
            height=400
        )
        return fig
    
    # Extract daily calories
    days = [f"Day {day['day']}" for day in meal_plan['days']]
    calories = [day['total_calories'] for day in meal_plan['days']]
    
    # Calculate target calories
    target_calories = meal_plan.get('daily_calories', 0)
    
    # Create the bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=days,
        y=calories,
        name='Daily Calories',
        marker_color='#4CAF50'
    ))
    
    if target_calories > 0:
        # Add target line
        fig.add_trace(go.Scatter(
            x=days,
            y=[target_calories] * len(days),
            mode='lines',
            name='Target Calories',
            line=dict(color='red', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title='Daily Calories in Meal Plan',
        xaxis_title='Day',
        yaxis_title='Calories',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        plot_bgcolor='white',
        yaxis=dict(gridcolor='lightgray')
    )
    
    return fig

def create_nutrient_comparison_chart(foods, nutrient='Protein'):
    """
    Create a horizontal bar chart comparing a specific nutrient across foods
    
    Parameters:
    - foods: List of food dictionaries with nutrient information
    - nutrient: The nutrient to compare (e.g., 'Protein', 'Carbs', 'Fat')
    
    Returns:
    - Plotly figure object
    """
    if not foods:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title=f'{nutrient} Comparison',
            xaxis_title=f'{nutrient} (g)',
            yaxis_title='Food',
            height=400
        )
        return fig
    
    # Convert nutrient name to lowercase for dictionary access
    nutrient_lower = nutrient.lower()
    
    # Extract food names and nutrient values
    food_names = [food['name'] for food in foods]
    nutrient_values = [food.get(nutrient_lower, 0) for food in foods]
    
    # Sort by nutrient value
    sorted_indices = np.argsort(nutrient_values)
    food_names = [food_names[i] for i in sorted_indices]
    nutrient_values = [nutrient_values[i] for i in sorted_indices]
    
    # Create the horizontal bar chart
    fig = go.Figure(go.Bar(
        y=food_names,
        x=nutrient_values,
        orientation='h',
        marker_color='#2196F3'
    ))
    
    fig.update_layout(
        title=f'{nutrient} Comparison',
        xaxis_title=f'{nutrient} (g)',
        yaxis_title='Food',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor='white',
        xaxis=dict(gridcolor='lightgray')
    )
    
    return fig

def create_exercise_distribution_chart(recommendations):
    """
    Create a pie chart showing distribution of exercise types
    
    Parameters:
    - recommendations: Dict containing exercise recommendations by category
    
    Returns:
    - Plotly figure object
    """
    if not recommendations:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title='Exercise Distribution',
            height=400
        )
        return fig
    
    # Count exercises by category
    categories = []
    counts = []
    
    for category, exercises in recommendations.items():
        if exercises:  # Only include non-empty categories
            categories.append(category)
            counts.append(len(exercises))
    
    # Create the pie chart
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=counts,
        hole=.3,
        textinfo='label+percent',
        marker=dict(colors=['#4CAF50', '#2196F3', '#FFC107'])
    )])
    
    fig.update_layout(
        title='Exercise Type Distribution',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig
