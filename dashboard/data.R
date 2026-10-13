library(shiny)
library(bslib)
library(DBI)
library(RMariaDB)
library(dplyr)
library(plotly)
library(scales)

# =========================
# DATABASE SETTINGS
# =========================
db_host <- Sys.getenv("DB_HOST", "127.0.0.1")
db_port <- as.numeric(Sys.getenv("DB_PORT", "3306"))
db_name <- Sys.getenv("DB_NAME", "waste_management")
db_user <- Sys.getenv("DB_USER", "db_user")
db_password <- Sys.getenv("DB_PASSWORD", "your_password_here")

# =========================
# DATABASE CONNECTION
# =========================
con <- dbConnect(
  RMariaDB::MariaDB(),
  host = db_host,
  port = db_port,
  dbname = db_name,
  user = db_user,
  password = db_password
)

# =========================
# HELPER FUNCTIONS
# =========================
fill_color <- function(fill_pct) {
  if (is.na(fill_pct)) return("#6b7280")
  if (fill_pct >= 80) return("#dc2626")
  if (fill_pct >= 50) return("#f59e0b")
  return("#16a34a")
}

fill_text <- function(fill_pct) {
  if (is.na(fill_pct)) return("No data")
  paste0(round(fill_pct, 1), "%")
}

make_hour_chart <- function(hour_data) {
  if (is.null(hour_data) || nrow(hour_data) == 0 || sum(hour_data$trash_count, na.rm = TRUE) == 0) {
    return(plot_ly() %>% layout(title = "No time-of-day data yet"))
  }
  
  plot_ly(
    data = hour_data,
    x = ~hour_label,
    y = ~trash_count,
    type = "bar",
    marker = list(color = "#0f766e"),
    hovertemplate = "%{x}<br>%{y} trash drops<extra></extra>"
  ) %>%
    layout(
      title = list(text = "Busiest Time of Day"),
      xaxis = list(title = "Hour"),
      yaxis = list(title = "Trash Drops"),
      margin = list(l = 60, r = 20, t = 50, b = 60)
    )
}

make_day_chart <- function(day_data) {
  if (is.null(day_data) || nrow(day_data) == 0 || sum(day_data$trash_count, na.rm = TRUE) == 0) {
    return(plot_ly() %>% layout(title = "No day-of-week data yet"))
  }
  
  plot_ly(
    data = day_data,
    x = ~day_name,
    y = ~trash_count,
    type = "bar",
    marker = list(color = "#f59e0b"),
    hovertemplate = "%{x}<br>%{y} trash drops<extra></extra>"
  ) %>%
    layout(
      title = list(text = "Busiest Day of Week"),
      xaxis = list(title = "Day"),
      yaxis = list(title = "Trash Drops"),
      margin = list(l = 60, r = 20, t = 50, b = 60)
    )
}

# =========================
# UI
# =========================
ui <- page_fluid(
  theme = bs_theme(
    version = 5,
    bootswatch = "flatly",
    primary = "#0f766e"
  ),
  
  tags$head(
    tags$style(HTML("
      body { background: #f8fafc; }
      .title-wrap { margin-bottom: 20px; }
      .dashboard-title { font-weight: 800; margin-bottom: 4px; }
      .dashboard-subtitle { color: #64748b; }
      .refresh-box {
        background: #ecfeff;
        border: 1px solid #a5f3fc;
        color: #155e75;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 24px;
        font-weight: 600;
      }
      .section-title {
        font-size: 22px;
        font-weight: 800;
        margin: 20px 0 14px 0;
        color: #0f172a;
      }
      .grid-4 {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .card-box {
        background: #ffffff;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0;
      }
      .wide-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
      }
      .card-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 8px;
        font-weight: 700;
      }
      .big-number {
        font-size: 28px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 10px;
      }
      .fill-wrap {
        width: 100%;
        height: 20px;
        background: #e5e7eb;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 8px;
      }
      .fill-bar {
        height: 100%;
        border-radius: 999px;
      }
      .percent-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
      }
      .meta-text {
        margin-top: 10px;
        font-size: 13px;
        color: #64748b;
      }
      @media (max-width: 992px) {
        .grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .grid-2 { grid-template-columns: 1fr; }
      }
      @media (max-width: 576px) {
        .grid-4 { grid-template-columns: 1fr; }
      }
    "))
  ),
  
  div(class = "title-wrap",
      h2(class = "dashboard-title", "Waste Management Dashboard"),
      div(class = "dashboard-subtitle", "Live compartment fill levels, total trash distribution, and busy-time trends")
  ),
  
  div(class = "refresh-box", textOutput("last_refresh", inline = TRUE)),
  
  div(class = "section-title", "Current Fill Percentages"),
  uiOutput("fill_cards"),
  
  div(class = "section-title", "Total Trash Distribution"),
  div(
    class = "wide-card",
    plotlyOutput("total_trash_pie", height = "420px")
  ),
  
  div(class = "section-title", "Trash Activity Trends"),
  div(
    class = "grid-2",
    div(class = "wide-card", plotlyOutput("busiest_hour_chart", height = "380px")),
    div(class = "wide-card", plotlyOutput("busiest_day_chart", height = "380px"))
  )
)

# =========================
# SERVER
# =========================
server <- function(input, output, session) {
  
  latest_fill <- reactivePoll(
    intervalMillis = 5000,
    session = session,
    checkFunc = function() {
      res <- dbGetQuery(con, "SELECT MAX(id) AS last_id FROM ultrasonic_readings")
      if (nrow(res) == 0) NA else res$last_id[1]
    },
    valueFunc = function() {
      dbGetQuery(con, "
        SELECT u.bin_id, u.fill_percent, u.distance_cm, u.reading_time, u.id
        FROM ultrasonic_readings u
        INNER JOIN (
          SELECT bin_id, MAX(id) AS max_id
          FROM ultrasonic_readings
          GROUP BY bin_id
        ) latest
        ON u.bin_id = latest.bin_id
        AND u.id = latest.max_id
        ORDER BY u.bin_id
      ")
    }
  )
  
  ir_counts <- reactivePoll(
    intervalMillis = 5000,
    session = session,
    checkFunc = function() {
      dbGetQuery(
        con,
        "SELECT COUNT(*) AS total_events FROM ir_sensor_events WHERE beam_broken = 1"
      )$total_events[1]
    },
    valueFunc = function() {
      dbGetQuery(con, "
        SELECT compartment_id, COUNT(*) AS trash_count, MAX(event_time) AS last_event
        FROM ir_sensor_events
        WHERE beam_broken = 1
        GROUP BY compartment_id
        ORDER BY compartment_id
      ")
    }
  )
  
  ir_events_all <- reactivePoll(
    intervalMillis = 5000,
    session = session,
    checkFunc = function() {
      res <- dbGetQuery(con, "SELECT MAX(event_time) AS last_time FROM ir_sensor_events WHERE beam_broken = 1")
      if (nrow(res) == 0) NA else res$last_time[1]
    },
    valueFunc = function() {
      dbGetQuery(con, "
        SELECT compartment_id, beam_broken, event_time
        FROM ir_sensor_events
        WHERE beam_broken = 1
        ORDER BY event_time
      ")
    }
  )
  
  fill_data_complete <- reactive({
    base_bins <- data.frame(bin_id = 1:4)
    latest <- latest_fill()
    
    if (is.null(latest) || nrow(latest) == 0) {
      return(base_bins %>%
               mutate(
                 fill_percent = NA_real_,
                 distance_cm = NA_real_,
                 reading_time = as.POSIXct(NA),
                 id = NA_integer_
               ))
    }
    
    base_bins %>% left_join(latest, by = "bin_id")
  })
  
  count_data_complete <- reactive({
    base_bins <- data.frame(compartment_id = 1:4)
    base_bins %>%
      left_join(ir_counts(), by = "compartment_id") %>%
      mutate(trash_count = ifelse(is.na(trash_count), 0, as.numeric(trash_count)))
  })
  
  hour_data <- reactive({
    events <- ir_events_all()
    if (is.null(events) || nrow(events) == 0) {
      return(data.frame(hour = integer(), hour_label = character(), trash_count = integer()))
    }
    
    events %>%
      mutate(hour = as.integer(format(as.POSIXct(event_time), "%H"))) %>%
      group_by(hour) %>%
      summarise(trash_count = n(), .groups = "drop") %>%
      arrange(hour) %>%
      mutate(hour_label = paste0(sprintf("%02d", hour), ":00"))
  })
  
  day_data <- reactive({
    events <- ir_events_all()
    if (is.null(events) || nrow(events) == 0) {
      return(data.frame(day_num = integer(), day_name = character(), trash_count = integer()))
    }
    
    day_levels <- c("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
    
    events %>%
      mutate(
        day_num = as.integer(format(as.POSIXct(event_time), "%w")),
        day_name = factor(day_levels[day_num + 1], levels = day_levels)
      ) %>%
      group_by(day_num, day_name) %>%
      summarise(trash_count = n(), .groups = "drop") %>%
      arrange(day_num)
  })
  
  output$last_refresh <- renderText({
    paste("Last refresh:", format(Sys.time(), "%Y-%m-%d %I:%M:%S %p"))
  })
  
  output$fill_cards <- renderUI({
    df <- fill_data_complete()
    
    cards <- lapply(seq_len(nrow(df)), function(i) {
      row <- df[i, ]
      pct <- ifelse(is.na(row$fill_percent), 0, max(0, min(100, as.numeric(row$fill_percent))))
      color <- fill_color(row$fill_percent)
      
      div(
        class = "card-box",
        div(class = "card-title", paste("Compartment", row$bin_id)),
        div(
          class = "percent-row",
          div(class = "big-number", style = paste0("color:", color, "; margin-bottom:0;"), fill_text(row$fill_percent)),
          div(class = "meta-text", style = "margin-top:0;", paste0(round(pct, 1), "% full"))
        ),
        div(
          class = "fill-wrap",
          div(class = "fill-bar", style = paste0("width:", pct, "%; background:", color, ";"))
        ),
        div(
          class = "meta-text",
          paste("Distance:", ifelse(is.na(row$distance_cm), "No data", paste0(round(as.numeric(row$distance_cm), 2), " cm")))
        ),
        div(
          class = "meta-text",
          paste("Updated:", ifelse(is.na(row$reading_time), "No data", as.character(row$reading_time)))
        )
      )
    })
    
    div(class = "grid-4", cards)
  })
  
  output$total_trash_pie <- renderPlotly({
    df <- count_data_complete()
    
    if (is.null(df) || nrow(df) == 0 || sum(df$trash_count, na.rm = TRUE) == 0) {
      return(plot_ly() %>% layout(title = "No trash data yet"))
    }
    
    plot_ly(
      data = df,
      type = "pie",
      labels = ~paste("Compartment", compartment_id),
      values = ~trash_count,
      textinfo = "label+percent",
      textposition = "inside",
      insidetextorientation = "horizontal",
      hovertemplate = paste(
        "%{label}",
        "<br>Trash drops: %{value}",
        "<br>Share: %{percent}",
        "<extra></extra>"
      ),
      marker = list(
        colors = c("#0f766e", "#14b8a6", "#f59e0b", "#dc2626"),
        line = list(color = "#ffffff", width = 2)
      ),
      sort = FALSE,
      showlegend = TRUE
    ) %>%
      layout(
        title = list(text = "Total Trash Distribution"),
        margin = list(l = 20, r = 20, t = 60, b = 40),
        legend = list(orientation = "h", x = 0.2, y = -0.05)
      )
  })
  
  output$busiest_hour_chart <- renderPlotly({
    make_hour_chart(hour_data())
  })
  
  output$busiest_day_chart <- renderPlotly({
    make_day_chart(day_data())
  })
}

# =========================
# CLEANUP
# =========================
onStop(function() {
  if (exists("con") && DBI::dbIsValid(con)) DBI::dbDisconnect(con)
})

shinyApp(ui = ui, server = server)
