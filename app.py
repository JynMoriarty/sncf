import streamlit as st 
import sqlite3
import csv 
import pandas as pd 
import plotly.express as px
import folium
from streamlit_folium import st_folium

APP_title = 'SNCF : Etude des objets perdus dans les régions de France'

df1 = pd.read_csv("sncf.csv")
df1.type = df1.type.astype('string')
connexion = sqlite3.connect('sncf.db')

# Récupérer les données à partir de la base de données
df1 = pd.read_sql_query("SELECT date, nature,type FROM Sncf", connexion)
df1['date'] = pd.to_datetime(df1['date']) - pd.to_timedelta(7, unit='d')

# Extraire l'année des dates
df1['annee'] = pd.DatetimeIndex(df1['date']).year

# Filtrer les données entre 2016 et 2021
df_filtre = df1[(df1['annee'] >= 2016) & (df1['annee'] <= 2021)]

# Calculer le nombre d'objets perdus par semaine
df_filtre['objet_perdu_semaine'] = df_filtre.groupby(pd.Grouper(key='date', freq='W'))['nature'].transform('count')

# Afficher le résultat
connexion.close()

def display_map (df,year,type):
    france=df.loc[(df['year']==year)&(df['type']==type)].groupby(['code_dep','type','year']).sum('lost_objet')
    france.reset_index(inplace=True)
    france.type = france.type.astype('string')
    france.lost_objet = france.lost_objet.astype('int')
    france.set_index('code_dep')
    map = folium.Map(location =(48.52,2.50),zoom_start=5.5,scrollWheelZoom = False ) 
    
    folium.Choropleth(
        geo_data='departements.geojson',
        data=france,
        columns=['code_dep','lost_objet'],
        key_on='feature.properties.code',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.1,
        highlight=True,
    ).add_to(map)
    st_folium(map,width=700,height=450)

typee= df1.type.unique().tolist()

st.set_page_config(APP_title)
st.title(APP_title)

st.write("Histogramme du total d'objet perdu par semaine de 2016-2021")
st.bar_chart(df_filtre.groupby(pd.Grouper(key='date', freq='W'))['objet_perdu_semaine'].count())
typo = st.selectbox("Choissiez un type d'objet perdu",typee)

if typo :
    connexion = sqlite3.connect('sncf.db')
    stmt = "SELECT * FROM Sncf WHERE type = '{}'".format(typo)
    df_restitution = pd.read_sql(stmt, connexion, parse_dates=True)
    df_restitution['date'] = pd.to_datetime(df_restitution['date'])
    df2 = df_restitution.groupby([pd.Grouper(key='date', freq='W-MON'),'type']).size().reset_index().rename(columns={'date' : 'week', 'id':'nb_lost_item'})
    fig = px.line(df2, x="week", y=0,title="Evolution du nombre d'objets type {} perdus sur la période 2016-2021".format(typo))

    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Nombre d'objets perdus",
        legend_title="Evolution d'objet type {} perdu entre 2016 et 2021".format(typo),
        showlegend=True
    )
    st.plotly_chart(fig)


df_map = pd.read_csv('map.csv',index_col=False)
st.write('Carte des objets perdus de type {} et la fréquence de voyageurs en fonction du temps dans les régions de france'.format(typo))
annee = st.selectbox('Année :',['2016','2017','2018','2019','2020','2021'])

display_map(df_map,annee,typo)

    


