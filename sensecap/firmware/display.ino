/*
 * display.ino — SenseCAP Indicator firmware for ScamShield
 *
 * Listens on USB serial for line-based commands from the Pi:
 *   STATUS:<text>\n   → update top status line
 *   TEXT:<text>\n     → update scrolling body text
 *
 * Display layout:
 *   ┌────────────────────────┐
 *   │ [STATUS LINE]          │  ← large bold text, colored by state
 *   │ [BODY TEXT]            │  ← smaller text, wraps
 *   └────────────────────────┘
 *
 * Background color:
 *   "SCAM DETECTED" → RED
 *   "ScamShield Ready" / "Call seems safe" → GREEN
 *   "Listening" → BLUE
 *   default → DARK GRAY
 */

#include <Arduino.h>
#include <lvgl.h>
#include <TFT_eSPI.h>

// Serial baud rate (must match SENSECAP_BAUD_RATE in Pi config.py)
#define SERIAL_BAUD 115200
#define MAX_LINE_LEN 256

// Display resolution (SenseCAP Indicator: 480×480)
#define SCREEN_W 480
#define SCREEN_H 480

// Colors
#define COLOR_RED    lv_color_hex(0xE53935)
#define COLOR_GREEN  lv_color_hex(0x43A047)
#define COLOR_BLUE   lv_color_hex(0x1E88E5)
#define COLOR_DARK   lv_color_hex(0x212121)
#define COLOR_WHITE  lv_color_hex(0xFFFFFF)
#define COLOR_YELLOW lv_color_hex(0xFDD835)

static TFT_eSPI tft = TFT_eSPI();

// LVGL display buffer
static lv_disp_draw_buf_t draw_buf;
static lv_color_t buf[SCREEN_W * 10];

// UI objects
static lv_obj_t *scr;
static lv_obj_t *status_label;
static lv_obj_t *body_label;
static lv_obj_t *bg_rect;

// Serial input buffer
static char serial_buf[MAX_LINE_LEN];
static int  serial_pos = 0;

// Current state
static char current_status[MAX_LINE_LEN] = "ScamShield Ready";
static char current_body[MAX_LINE_LEN]   = "Monitoring for scam calls...";


// ── LVGL display flush ────────────────────────────────────────────────────────

static void my_disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p) {
    uint32_t w = area->x2 - area->x1 + 1;
    uint32_t h = area->y2 - area->y1 + 1;
    tft.startWrite();
    tft.setAddrWindow(area->x1, area->y1, w, h);
    tft.pushColors((uint16_t *)&color_p->full, w * h, true);
    tft.endWrite();
    lv_disp_flush_ready(disp);
}


// ── UI helpers ────────────────────────────────────────────────────────────────

static lv_color_t _bg_color_for_status(const char *status) {
    if (strstr(status, "SCAM") != NULL || strstr(status, "DETECTED") != NULL) {
        return COLOR_RED;
    }
    if (strstr(status, "Ready") != NULL || strstr(status, "safe") != NULL) {
        return COLOR_GREEN;
    }
    if (strstr(status, "Listen") != NULL || strstr(status, "Analyz") != NULL) {
        return COLOR_BLUE;
    }
    return COLOR_DARK;
}

static void _refresh_display() {
    lv_color_t bg = _bg_color_for_status(current_status);
    lv_obj_set_style_bg_color(scr, bg, 0);
    lv_label_set_text(status_label, current_status);
    lv_label_set_text(body_label, current_body);
    lv_refr_now(NULL);
}


// ── Serial command parser ─────────────────────────────────────────────────────

static void _handle_command(const char *line) {
    if (strncmp(line, "STATUS:", 7) == 0) {
        strncpy(current_status, line + 7, MAX_LINE_LEN - 1);
        current_status[MAX_LINE_LEN - 1] = '\0';
        _refresh_display();
    } else if (strncmp(line, "TEXT:", 5) == 0) {
        strncpy(current_body, line + 5, MAX_LINE_LEN - 1);
        current_body[MAX_LINE_LEN - 1] = '\0';
        _refresh_display();
    }
    // Unknown commands are silently ignored
}

static void _poll_serial() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (serial_pos > 0) {
                serial_buf[serial_pos] = '\0';
                _handle_command(serial_buf);
                serial_pos = 0;
            }
        } else {
            if (serial_pos < MAX_LINE_LEN - 1) {
                serial_buf[serial_pos++] = c;
            }
            // overflow: silently drop
        }
    }
}


// ── Setup ─────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(SERIAL_BAUD);

    // TFT init
    tft.begin();
    tft.setRotation(0);

    // LVGL init
    lv_init();
    lv_disp_draw_buf_init(&draw_buf, buf, NULL, SCREEN_W * 10);

    static lv_disp_drv_t disp_drv;
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res  = SCREEN_W;
    disp_drv.ver_res  = SCREEN_H;
    disp_drv.flush_cb = my_disp_flush;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);

    // Screen
    scr = lv_scr_act();
    lv_obj_set_style_bg_color(scr, COLOR_GREEN, 0);
    lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);

    // Status label (top, large)
    status_label = lv_label_create(scr);
    lv_obj_set_width(status_label, SCREEN_W - 40);
    lv_obj_align(status_label, LV_ALIGN_TOP_MID, 0, 60);
    lv_label_set_long_mode(status_label, LV_LABEL_LONG_WRAP);
    lv_obj_set_style_text_color(status_label, COLOR_WHITE, 0);
    lv_obj_set_style_text_font(status_label, &lv_font_montserrat_28, 0);
    lv_obj_set_style_text_align(status_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_label_set_text(status_label, current_status);

    // Body label (bottom, smaller)
    body_label = lv_label_create(scr);
    lv_obj_set_width(body_label, SCREEN_W - 40);
    lv_obj_align(body_label, LV_ALIGN_TOP_MID, 0, 200);
    lv_label_set_long_mode(body_label, LV_LABEL_LONG_SCROLL_CIRCULAR);
    lv_obj_set_style_text_color(body_label, COLOR_WHITE, 0);
    lv_obj_set_style_text_font(body_label, &lv_font_montserrat_16, 0);
    lv_obj_set_style_text_align(body_label, LV_TEXT_ALIGN_CENTER, 0);
    lv_label_set_text(body_label, current_body);

    _refresh_display();
}


// ── Loop ──────────────────────────────────────────────────────────────────────

void loop() {
    _poll_serial();
    lv_timer_handler();
    delay(5);
}
