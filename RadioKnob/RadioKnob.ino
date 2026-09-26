#include <Arduino.h>
#include "USB.h"
#include "USBMIDI.h"
#include "tusb.h"
#include "lcd_bsp.h"
#include "cst816.h"
#include "lcd_bl_pwm_bsp.h"
#include "bidi_switch_knob.h"

USBMIDI midi;
static QueueHandle_t turns;
static lv_obj_t *connectionLabel, *motionLabel, *speedLabel, *frequencyLabel;
static uint32_t frequencyHz = 0;
static unsigned long lastFrequency = 0;
static bool frequencyLive = false;
static volatile bool fastMode = false;
static long totalTurns = 0;
static unsigned long lastTurn = 0;
static bool wasMounted = false;
static void left(void *, void *) { int8_t d=-1; xQueueSend(turns,&d,0); }
static void right(void *, void *) { int8_t d=1; xQueueSend(turns,&d,0); }
static void toggleSpeed(lv_event_t *) {
  fastMode=!fastMode;
  lv_label_set_text(speedLabel,fastMode?"FAST  x10":"FINE  x1");
}
static lv_obj_t *label(const char *text, int y, const lv_font_t *font, uint32_t color) {
  lv_obj_t *l=lv_label_create(lv_scr_act());
  lv_label_set_text(l,text);
  lv_obj_set_style_text_font(l,font,0);
  lv_obj_set_style_text_color(l,lv_color_hex(color),0);
  lv_obj_align(l,LV_ALIGN_CENTER,0,y);
  return l;
}
void setup() {
  USB.productName("Dan's Radio Dial");
  USB.manufacturerName("RadioKnob");
  midi.begin();
  Serial.begin(115200);
  USB.begin();
  Touch_Init();
  lcd_lvgl_Init();
  lcd_bl_pwm_bsp_init(200);
  if(example_lvgl_lock(-1)) {
    lv_obj_set_style_bg_color(lv_scr_act(),lv_color_hex(0x091722),0);
    lv_obj_set_style_bg_opa(lv_scr_act(),LV_OPA_COVER,0);
    label("DAN'S RADIO DIAL",-110,&lv_font_montserrat_20,0x69dfce);
    frequencyLabel=label("---.---.---",-48,&lv_font_montserrat_32,0xffffff);
    label("MHz",-18,&lv_font_montserrat_20,0x69dfce);
    connectionLabel=label("Waiting for radio",10,&lv_font_montserrat_20,0xa5bcca);
    motionLabel=label("Turn ring to tune",42,&lv_font_montserrat_20,0xffffff);
    lv_obj_t *button=lv_btn_create(lv_scr_act());
    lv_obj_set_size(button,170,48);lv_obj_align(button,LV_ALIGN_CENTER,0,92);
    lv_obj_set_style_bg_color(button,lv_color_hex(0x185369),0);
    lv_obj_add_event_cb(button,toggleSpeed,LV_EVENT_CLICKED,NULL);
    speedLabel=lv_label_create(button);lv_label_set_text(speedLabel,"FINE  x1");
    lv_obj_set_style_text_font(speedLabel,&lv_font_montserrat_20,0);lv_obj_center(speedLabel);
    example_lvgl_unlock();
  }
  turns=xQueueCreate(64,sizeof(int8_t));
  knob_config_t config={.gpio_encoder_a=8,.gpio_encoder_b=7};
  knob_handle_t knob=iot_knob_create(&config);
  ESP_ERROR_CHECK(knob?ESP_OK:ESP_FAIL);
  ESP_ERROR_CHECK(iot_knob_register_cb(knob,KNOB_LEFT,left,NULL));
  ESP_ERROR_CHECK(iot_knob_register_cb(knob,KNOB_RIGHT,right,NULL));
  Serial.println("RADIO_DIAL_READY v1.2 USB MIDI CC16 relative 65/63");
}
void loop() {
  const bool mounted=tud_mounted();
  if(mounted!=wasMounted) {
    wasMounted=mounted;
    if(example_lvgl_lock(50)) {
      lv_label_set_text(connectionLabel,mounted?"Waiting for radio":"Connect USB to Mac");
      example_lvgl_unlock();
    }
  }
  int8_t d;
  if(xQueueReceive(turns,&d,pdMS_TO_TICKS(5))==pdTRUE) {
    totalTurns+=d;lastTurn=millis();
    // DJ2GO2 relative encoding: 64 is neutral; 65/63 mean one step.
    if(mounted) midi.controlChange(16,64+d*(fastMode?10:1),1);
    Serial.printf("TURN %d total=%ld connected=%d\n",d,totalTurns,mounted);
    if(example_lvgl_lock(50)) {
      lv_label_set_text(motionLabel,d>0?"Tuning UP  >":"<  Tuning DOWN");
      example_lvgl_unlock();
    }
  }
  if(lastTurn && millis()-lastTurn>1000) {
    lastTurn=0;
    if(example_lvgl_lock(50)) {lv_label_set_text(motionLabel,"Turn ring to tune");example_lvgl_unlock();}
  }
  if(frequencyLive && (!mounted || millis()-lastFrequency>3000)) {
    if(example_lvgl_lock(50)) {
      frequencyLive=false;
      lv_label_set_text(frequencyLabel,"---.---.---");
      lv_label_set_text(connectionLabel,"Waiting for radio");
      example_lvgl_unlock();
    }
  }
  static String cmd;
  static bool overflow=false;
  while(Serial.available()) {
    char c=Serial.read();
    if(c=='\n') {
      if(!overflow && cmd=="STATUS")
        Serial.printf("RADIO_DIAL v1.2 midi=%d turns=%ld fast=%d frequency=%lu live=%d\n",mounted,totalTurns,fastMode,(unsigned long)frequencyHz,frequencyLive);
      else if(!overflow && cmd.startsWith("FREQ ")) {
        bool valid=cmd.length()>5 && cmd.length()<=15;
        for(unsigned int i=5;i<cmd.length();i++) if(cmd[i]<'0'||cmd[i]>'9')valid=false;
        uint64_t hz=valid?strtoull(cmd.c_str()+5,NULL,10):0;
        if(hz>0 && hz<=999999999 && example_lvgl_lock(50)) {
          frequencyHz=(uint32_t)hz;lastFrequency=millis();frequencyLive=true;
          char display[24];
          snprintf(display,sizeof(display),"%lu.%03lu.%03lu",(unsigned long)(frequencyHz/1000000),(unsigned long)((frequencyHz/1000)%1000),(unsigned long)(frequencyHz%1000));
          lv_label_set_text(frequencyLabel,display);
          lv_label_set_text(connectionLabel,"Live radio frequency");
          example_lvgl_unlock();
        }
      }
      cmd="";overflow=false;
    } else if(c!='\r') {
      if(cmd.length()<48)cmd+=c;else overflow=true;
    }
  }
}
