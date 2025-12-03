import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
st.set_page_config(layout="wide", page_title="Tesla Production and Delivery Analytics")

DB_PATH = "ev_data.db"


MONTH_ORDER = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12}

@st.cache_data
def run_query(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

st.title("⚡ Tesla Production & Delivery Analytics Dashboard")
st.markdown("**Team 6: Object Oriented Leaders (OOLs)**")
st.divider()

st.sidebar.header("Dashboard Filters")

year_options = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
selected_years = st.sidebar.multiselect(
    "Select Year(s):",
    options=year_options,
    default=[2024])

model_options = ["Model S", "Model 3", "Model X", "Model Y", "Cybertruck"]
selected_models = st.sidebar.multiselect(
    "Select Model(s):",
    options=model_options,
    default=["Model S"])

region_options = ["North America", "Europe", "Asia", "Middle East"]
selected_regions = st.sidebar.multiselect(
    "Select Region(s):",
    options=region_options,
    default=["North America"])
st.sidebar.divider()

st.header("📊 Key Performance Metrics")

if selected_years and selected_models and selected_regions:
    metrics_query = """
    SELECT 
        SUM(production_units) as total_production,
        SUM(estimated_deliveries) as total_deliveries,
        AVG(avg_price_usd) as avg_price
    FROM EVMetrics f
    JOIN Date d ON f.date_id = d.date_id
    JOIN Model m ON f.model_id = m.model_id
    JOIN Region r ON f.region_id = r.region_id
    WHERE d.year IN ({years})
        AND m.model_name IN ({models})
        AND r.region_name IN ({regions})
    """.format(
        years=",".join(map(str, selected_years)),
        models=",".join([f"'{m}'" for m in selected_models]),
        regions=",".join([f"'{r}'" for r in selected_regions])
    )
    
    df_metrics = run_query(metrics_query)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if df_metrics is not None and not df_metrics.empty:
            total_prod = df_metrics['total_production'].iloc[0]
            st.metric(label="Total Production", value=f"{total_prod:,.0f}" if pd.notna(total_prod) else "N/A")
        else:
            st.metric(label="Total Production", value="No Data")
    
    with col2:
        if df_metrics is not None and not df_metrics.empty:
            total_deliv = df_metrics['total_deliveries'].iloc[0]
            st.metric(label="Total Deliveries", value=f"{total_deliv:,.0f}" if pd.notna(total_deliv) else "N/A")
        else:
            st.metric(label="Total Deliveries", value="No Data")
    
    with col3:
        if df_metrics is not None and not df_metrics.empty:
            avg_price = df_metrics['avg_price'].iloc[0]
            st.metric(label="Avg Price (USD)", value=f"${avg_price:,.2f}" if pd.notna(avg_price) else "N/A")
        else:
            st.metric(label="Avg Price (USD)", value="No Data")
else:
    st.warning("Please select at least one option from each filter")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Production & Delivery Analysis", 
    "Regional Pricing Analysis", 
    "Growth Rates & Seasonality Analysis", 
    "Delivery & Infrastructure Analysis", 
    "Market Trend Analysis"
])

with tab1:
    st.header("🔧 Production Volatility & Delivery Performance")
    
    if selected_years and selected_models and selected_regions:
        st.subheader("Which models show the most volatile production changes?")
        
        volatility_query = """
        SELECT 
            m.model_name,
            d.year,
            d.month_name,
            f.production_units,
            f.estimated_deliveries
        FROM EVMetrics f
        JOIN Model m ON f.model_id = m.model_id
        JOIN Date d ON f.date_id = d.date_id
        JOIN Region r ON f.region_id = r.region_id
        WHERE d.year IN ({years})
            AND m.model_name IN ({models})
            AND r.region_name IN ({regions})
        """.format(
            years=",".join(map(str, selected_years)),
            models=",".join([f"'{m}'" for m in selected_models]),
            regions=",".join([f"'{r}'" for r in selected_regions])
        )
        
        df_volatility = run_query(volatility_query)
        
        if df_volatility is not None and not df_volatility.empty:
            df_volatility['month_order'] = df_volatility['month_name'].map(MONTH_ORDER)
            df_volatility = df_volatility.sort_values(['model_name', 'year', 'month_order'])
            df_volatility['prev_production'] = df_volatility.groupby('model_name')['production_units'].shift(1)
            df_volatility['pct_change'] = ((df_volatility['production_units'] - df_volatility['prev_production']) 
                                            / df_volatility['prev_production'] * 100)
            
            df_volatility['date'] = pd.to_datetime(df_volatility['year'].astype(str) + '-' + df_volatility['month_order'].astype(str) + '-01')

            fig_volatility = px.line(
                df_volatility,
                x='date',
                y='pct_change',
                color='model_name',
                title='Annual Month-over-Month Production Volatility by Model (%)',
                labels={'pct_change': 'Production Change (%)', 'date': 'Year'}
            )

            fig_volatility.update_xaxes(
                dtick="M12",           # Show tick every 12 months (yearly)
                tickformat="%Y",       # Display only the year
                ticklabelmode="period" # Center year over its 12 months
            )

            st.plotly_chart(fig_volatility, use_container_width=True)
            
            st.markdown("""
            **Business Insight:** Production volatility analysis reveals which models face the most unpredictable 
            manufacturing challenges. High volatility typically indicates supply chain disruptions, demand forecasting 
            issues, or production ramp-up/down challenges. Models with consistent production patterns demonstrate 
            operational maturity, while volatile models may require supply chain optimization or better demand forecasting 
            to improve operational efficiency and reduce inventory carrying costs.
            """)
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_volatility, width='stretch')
        else:
            st.warning("No data available for selected filters.")
        
        st.divider()
        
        st.subheader("Production-Delivery Gap Analysis")
        
        gap_query = """
        SELECT 
            d.year,
            d.month_name,
            m.model_name,
            f.production_units,
            f.estimated_deliveries,
            (f.production_units - f.estimated_deliveries) as inventory_change
        FROM EVMetrics f
        JOIN Model m ON f.model_id = m.model_id
        JOIN Date d ON f.date_id = d.date_id
        JOIN Region r ON f.region_id = r.region_id
        WHERE d.year IN ({years})
            AND m.model_name IN ({models})
            AND r.region_name IN ({regions})
        """.format(
            years=",".join(map(str, selected_years)),
            models=",".join([f"'{m}'" for m in selected_models]),
            regions=",".join([f"'{r}'" for r in selected_regions])
        )
        
        df_gap = run_query(gap_query)
        
        if df_gap is not None and not df_gap.empty:
            df_gap['month_order'] = df_gap['month_name'].map(MONTH_ORDER)
            df_gap = df_gap.sort_values(['year', 'month_order'])
            
            df_gap['date'] = pd.to_datetime(df_gap['year'].astype(str) + '-' + df_gap['month_order'].astype(str) + '-01')

            fig_gap = go.Figure()
            

            
            fig_gap.add_trace(go.Scatter(
                x=df_gap['date'],  # ← Change from 'month_name' to 'date'
                y=df_gap['estimated_deliveries'],
                name='Deliveries',
                mode='lines+markers',
                marker_color='red'
            ))
            
            fig_gap.update_layout(
                title='Production vs Delivery Gap Over Time',
                xaxis_title='Year',
                yaxis_title='Units',
                hovermode='x unified'
            )
            
            # Add this to format the x-axis like the volatility graph
            fig_gap.update_xaxes(
                dtick="M12",
                tickformat="%Y",
                ticklabelmode="period"
            )
            
            st.plotly_chart(fig_gap, use_container_width=True)
            
            st.markdown("""
            **Business Insight:** The production-delivery gap reveals Tesla's inventory management effectiveness and demand 
            forecasting accuracy. Positive gaps (production > deliveries) indicate inventory buildup, potentially signaling 
            overproduction or softening demand. Negative gaps suggest strong demand outpacing supply or strategic inventory 
            drawdown. Consistent positive gaps may require production adjustments or enhanced marketing efforts, while 
            persistent negative gaps could indicate capacity constraints limiting revenue potential.
            """)
            
            st.write("### Key Insights:")
            avg_gap = df_gap.groupby('model_name')['inventory_change'].mean().reset_index()
            avg_gap.columns = ['Model', 'Average Inventory Change']
            st.dataframe(avg_gap, width='stretch')
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_gap, width='stretch')
        else:
            st.warning("No data available for selected filters.")

with tab2:
    st.header("🌍 Regional Pricing Analysis")
    
    if selected_years:
        st.subheader("Does mileage range affect regional sales?")
        
        range_query = """
        SELECT 
            r.region_name,
            m.model_name,
            f.range_km,
            SUM(f.estimated_deliveries) as total_deliveries
        FROM EVMetrics f
        JOIN Region r ON f.region_id = r.region_id
        JOIN Model m ON f.model_id = m.model_id
        JOIN Date d ON f.date_id = d.date_id
        WHERE d.year IN ({years})
        GROUP BY r.region_name, m.model_name, f.range_km
        """.format(years=",".join(map(str, selected_years)))
        
        df_range = run_query(range_query)
        
        if df_range is not None and not df_range.empty:
            fig_range = px.scatter(
                df_range,
                x='range_km',
                y='total_deliveries',
                color='region_name',
                size='total_deliveries',
                hover_data=['model_name'],
                title='Deliveries vs Vehicle Range by Region',
                labels={'range_km': 'Range (km)', 'total_deliveries': 'Total Deliveries'}
            )
            st.plotly_chart(fig_range, width='stretch')
            
            st.markdown("""
            **Business Insight:** Vehicle range significantly impacts regional purchasing decisions. Markets with extensive 
            geographic distances (e.g., North America) typically show higher demand for longer-range models, while dense 
            urban markets (e.g., Europe, Asia) may prioritize other factors. Understanding range preferences by region 
            enables targeted product positioning and helps optimize inventory allocation to match regional consumer needs.
            """)
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_range, width='stretch')
        else:
            st.warning("No data available for selected filters.")
        
        st.divider()
        
        st.subheader("Are average prices the same across different regions?")
        
        price_query = """
        SELECT 
            r.region_name,
            m.model_name,
            AVG(f.avg_price_usd) as avg_price
        FROM EVMetrics f
        JOIN Region r ON f.region_id = r.region_id
        JOIN Model m ON f.model_id = m.model_id
        JOIN Date d ON f.date_id = d.date_id
        WHERE d.year IN ({years})
        GROUP BY r.region_name, m.model_name
        """.format(years=",".join(map(str, selected_years)))
        
        df_price = run_query(price_query)
        
        if df_price is not None and not df_price.empty:
            fig_price = px.bar(
                df_price,
                x='region_name',
                y='avg_price',
                color='model_name',
                title='Average Price by Region and Model',
                labels={'avg_price': 'Average Price (USD)', 'region_name': 'Region'},
                barmode='group'
            )
            st.plotly_chart(fig_price, width='stretch')
            
            st.markdown("""
            **Business Insight:** Regional price variations reflect local market conditions, import duties, taxes, and 
            competitive dynamics. Significant price differences for the same model across regions may indicate arbitrage 
            opportunities or market inefficiencies. Understanding these variations enables strategic pricing decisions, 
            helps identify high-margin markets, and informs expansion strategies into underserved or premium markets.
            """)
            
            pivot_price = df_price.pivot(index='model_name', columns='region_name', values='avg_price')
            st.write("### Price Comparison Table")
            st.dataframe(pivot_price.style.format("${:,.2f}"), width='stretch')
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_price, width='stretch')
        else:
            st.warning("No data available for selected filters.")

with tab3:
    st.header("📈 Growth Rates & Seasonality")
    
    if selected_models and selected_regions:
        st.subheader("What are the quarter-over-quarter growth rates?")
        
        growth_query = """
        SELECT 
            d.year,
            d.month_name,
            SUM(f.production_units) as total_production,
            SUM(f.estimated_deliveries) as total_deliveries
        FROM EVMetrics f
        JOIN Date d ON f.date_id = d.date_id
        JOIN Model m ON f.model_id = m.model_id
        JOIN Region r ON f.region_id = r.region_id
        WHERE m.model_name IN ({models})
            AND r.region_name IN ({regions})
        GROUP BY d.year, d.month_name
        """.format(
            models=",".join([f"'{m}'" for m in selected_models]),
            regions=",".join([f"'{r}'" for r in selected_regions])
        )
        
        df_growth = run_query(growth_query)
        
        if df_growth is not None and not df_growth.empty:
            df_growth['month_order'] = df_growth['month_name'].map(MONTH_ORDER)
            df_growth = df_growth.sort_values(['year', 'month_order'])
            
            df_growth['prev_production'] = df_growth['total_production'].shift(1)
            df_growth['prev_deliveries'] = df_growth['total_deliveries'].shift(1)
            df_growth['prod_growth'] = ((df_growth['total_production'] - df_growth['prev_production']) 
                                         / df_growth['prev_production'] * 100)
            df_growth['deliv_growth'] = ((df_growth['total_deliveries'] - df_growth['prev_deliveries']) 
                                          / df_growth['prev_deliveries'] * 100)
            
            fig_growth = go.Figure()
            fig_growth.add_trace(go.Scatter(
                x=df_growth['month_name'],
                y=df_growth['prod_growth'],
                name='Production Growth',
                mode='lines+markers'
            ))
            fig_growth.add_trace(go.Scatter(
                x=df_growth['month_name'],
                y=df_growth['deliv_growth'],
                name='Delivery Growth',
                mode='lines+markers'
            ))
            
            fig_growth.update_layout(
                title='Month-over-Month Growth Rates (%)',
                xaxis_title='Month',
                yaxis_title='Growth Rate (%)',
                hovermode='x unified'
            )
            st.plotly_chart(fig_growth, width='stretch')
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_growth, width='stretch')
        else:
            st.warning("No data available for selected filters.")
        
        st.divider()
        
        st.subheader("Can we identify seasonal patterns?")
        
        if selected_years:
            seasonal_query = """
            SELECT 
                d.month_name,
                m.model_name,
                AVG(f.production_units) as avg_production,
                AVG(f.estimated_deliveries) as avg_deliveries
            FROM EVMetrics f
            JOIN Date d ON f.date_id = d.date_id
            JOIN Model m ON f.model_id = m.model_id
            JOIN Region r ON f.region_id = r.region_id
            WHERE d.year IN ({years})
                AND m.model_name IN ({models})
                AND r.region_name IN ({regions})
            GROUP BY d.month_name, m.model_name
            """.format(
                years=",".join(map(str, selected_years)),
                models=",".join([f"'{m}'" for m in selected_models]),
                regions=",".join([f"'{r}'" for r in selected_regions])
            )
            
            df_seasonal = run_query(seasonal_query)
            
            if df_seasonal is not None and not df_seasonal.empty:
                df_seasonal['month_order'] = df_seasonal['month_name'].map(MONTH_ORDER)
                df_seasonal = df_seasonal.sort_values('month_order')
                
                fig_seasonal = px.line(
                    df_seasonal,
                    x='month_name',
                    y='avg_production',
                    color='model_name',
                    title='Average Monthly Production by Model (Seasonal Pattern)',
                    labels={'avg_production': 'Average Production Units', 'month_name': 'Month'},
                    category_orders={"month_name": sorted(df_seasonal['month_name'].unique(), 
                                                           key=lambda x: MONTH_ORDER[x])}
                )
                st.plotly_chart(fig_seasonal, width='stretch')
                
                fig_seasonal2 = px.line(
                    df_seasonal,
                    x='month_name',
                    y='avg_deliveries',
                    color='model_name',
                    title='Average Monthly Deliveries by Model (Seasonal Pattern)',
                    labels={'avg_deliveries': 'Average Deliveries', 'month_name': 'Month'},
                    category_orders={"month_name": sorted(df_seasonal['month_name'].unique(), 
                                                           key=lambda x: MONTH_ORDER[x])}
                )
                st.plotly_chart(fig_seasonal2, width='stretch')
                
                with st.expander("📊 View Raw Data"):
                    st.dataframe(df_seasonal, width='stretch')
            else:
                st.warning("No data available for selected filters.")

with tab4:
    st.header("🚗 Delivery & Infrastructure Analysis")
    
    if selected_years:
        st.subheader("How does region affect estimated delivery?")
        
        regional_delivery_query = """
        SELECT 
            r.region_name,
            m.model_name,
            AVG(f.estimated_deliveries) as avg_deliveries,
            SUM(f.estimated_deliveries) as total_deliveries
        FROM EVMetrics f
        JOIN Region r ON f.region_id = r.region_id
        JOIN Model m ON f.model_id = m.model_id
        JOIN Date d ON f.date_id = d.date_id
        WHERE d.year IN ({years})
        GROUP BY r.region_name, m.model_name
        """.format(years=",".join(map(str, selected_years)))
        
        df_regional_delivery = run_query(regional_delivery_query)
        
        if df_regional_delivery is not None and not df_regional_delivery.empty:
            fig_regional = px.bar(
                df_regional_delivery,
                x='region_name',
                y='total_deliveries',
                color='model_name',
                title='Total Deliveries by Region and Model',
                labels={'total_deliveries': 'Total Deliveries', 'region_name': 'Region'},
                barmode='group'
            )
            st.plotly_chart(fig_regional, width='stretch')
            
            pivot_regional = df_regional_delivery.pivot(index='model_name', columns='region_name', values='avg_deliveries')
            st.write("### Average Deliveries by Region")
            st.dataframe(pivot_regional.style.format("{:,.0f}"), width='stretch')
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_regional_delivery, width='stretch')
        else:
            st.warning("No data available for selected filters.")
        
        st.divider()
        
        st.subheader("Does charging station availability affect sales?")
        
        charging_query = """
        SELECT 
            r.region_name,
            AVG(f.charging_stations) as avg_charging_stations,
            SUM(f.estimated_deliveries) as total_deliveries
        FROM EVMetrics f
        JOIN Region r ON f.region_id = r.region_id
        JOIN Date d ON f.date_id = d.date_id
        WHERE d.year IN ({years})
        GROUP BY r.region_name
        """.format(years=",".join(map(str, selected_years)))
        
        df_charging = run_query(charging_query)
        
        if df_charging is not None and not df_charging.empty:
            fig_charging = px.scatter(
                df_charging,
                x='avg_charging_stations',
                y='total_deliveries',
                text='region_name',
                size='total_deliveries',
                title='Charging Station Availability vs Deliveries',
                labels={'avg_charging_stations': 'Average Charging Stations', 
                       'total_deliveries': 'Total Deliveries'}
            )
            fig_charging.update_traces(textposition='top center')
            st.plotly_chart(fig_charging, width='stretch')
            
            correlation = df_charging[['avg_charging_stations', 'total_deliveries']].corr().iloc[0, 1]
            st.write(f"### Correlation: {correlation:.3f}")
            
            with st.expander("📊 View Raw Data"):
                st.dataframe(df_charging, width='stretch')
        else:
            st.warning("No data available for selected filters.")

with tab5:
    st.header("📈📉 Market Trend Analysis")
    
    st.subheader("Correlation between sales and EV infrastructure?")
    
    infra_corr_query = """
    SELECT 
        d.year,
        r.region_name,
        AVG(f.charging_stations) as avg_charging_stations,
        SUM(f.estimated_deliveries) as total_deliveries
    FROM EVMetrics f
    JOIN Region r ON f.region_id = r.region_id
    JOIN Date d ON f.date_id = d.date_id
    GROUP BY d.year, r.region_name
    """
    
    df_infra = run_query(infra_corr_query)
    
    if df_infra is not None and not df_infra.empty:
        fig_infra = px.scatter(
            df_infra,
            x='avg_charging_stations',
            y='total_deliveries',
            color='region_name',
            size='total_deliveries',
            hover_data=['year'],
            title='EV Infrastructure vs Sales Across Years and Regions',
            labels={'avg_charging_stations': 'Average Charging Stations', 
                   'total_deliveries': 'Total Deliveries'}
        )
        st.plotly_chart(fig_infra, width='stretch')
        
        for region in df_infra['region_name'].unique():
            region_data = df_infra[df_infra['region_name'] == region]
            if len(region_data) > 1:
                corr = region_data[['avg_charging_stations', 'total_deliveries']].corr().iloc[0, 1]
                st.write(f"**{region}** - Correlation: {corr:.3f}")
        
        with st.expander("📊 View Raw Data"):
            st.dataframe(df_infra, width='stretch')
    else:
        st.warning("No data available.")
    
    st.divider()
    
    st.subheader("Does Tesla sales reflect the EV industry shift?")
    
    trend_query = """
    SELECT 
        d.year,
        SUM(f.estimated_deliveries) as total_deliveries,
        SUM(f.production_units) as total_production,
        AVG(f.avg_price_usd) as avg_price
    FROM EVMetrics f
    JOIN Date d ON f.date_id = d.date_id
    GROUP BY d.year
    """
    
    df_trend = run_query(trend_query)
    
    if df_trend is not None and not df_trend.empty:
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Bar(
            x=df_trend['year'],
            y=df_trend['total_deliveries'],
            name='Total Deliveries',
            yaxis='y',
            marker_color='lightblue'
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=df_trend['year'],
            y=df_trend['avg_price'],
            name='Average Price',
            yaxis='y2',
            mode='lines+markers',
            marker_color='red'
        ))
        
        fig_trend.update_layout(
            title='Tesla Sales Growth Over Time',
            xaxis_title='Year',
            yaxis=dict(title='Total Deliveries', side='left'),
            yaxis2=dict(title='Average Price (USD)', side='right', overlaying='y'),
            hovermode='x unified'
        )
        st.plotly_chart(fig_trend, width='stretch')
        
        if len(df_trend) > 1:
            yoy_growth = ((df_trend['total_deliveries'].iloc[-1] - df_trend['total_deliveries'].iloc[0]) 
                         / df_trend['total_deliveries'].iloc[0] * 100)
            st.write(f"### Overall Growth: {yoy_growth:.1f}% from {df_trend['year'].iloc[0]} to {df_trend['year'].iloc[-1]}")
        
        with st.expander("📊 View Raw Data"):
            st.dataframe(df_trend, width='stretch')
    else:
        st.warning("No data available.")

st.divider()
st.caption("_Dashboard developed by Team 6: Object Oriented Leaders (OOLs)_")
st.caption("_Data Source: Tesla EA Deliveries and Production Data (2015-2025)_")