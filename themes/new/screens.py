__all__ = ['actions', 'widgets']

# for each screen:
# x,y,x2,y2 : printer_action_name

actions = [
    {
        (405, 13, 465, 107): 'ui_main_page',
        (405, 111, 468, 307): 'ui_next_page',
        (31 , 92, 119 , 170): 'halt',
        (10, 10, 125, 75) : 'quit',
        (180, 41, 250, 136): 'pause',
        (299, 37, 365, 145): 'connect',
        },
    {
        (453, 1, 478, 315): 'ui_main_page',
#        (405, 111, 468, 307): 'ui_next_page',
        (201, 18, 293, 108): 'home',
        (101, 127, 175, 202): 'home_xy',
        (374, 139, 425, 189): 'home_z',
        (95, 33, 190, 114): 'y_up',
        (90, 217, 190, 301): 'y_down',
        (5, 123, 86, 208): 'x_down',
        (175, 122, 274, 217) : 'x_up',
        (348, 34, 454, 120): 'z_up',
        (345, 212, 450, 305): 'z_down',
        (297, 104, 348, 157): 'z_up_small',
        (295, 174, 347, 232): 'z_down_small',
        },
    {
        (453, 1, 478, 315): 'ui_main_page',
#        (405, 111, 468, 307): 'ui_next_page',
        (26, 52, 145, 161): 'e_temp_up',
        (28, 207, 160, 280): 'e_temp_down',
        (168, 44, 289, 159): 'bed_temp_up',
        (172, 205, 301, 278): 'bed_temp_down',
        (324, 44, 453, 165): 'fan_up',
        (319, 203, 453, 292): 'fan_down',
        },
    {
        (453, 1, 478, 315): 'ui_main_page',
#        (405, 111, 468, 307): 'ui_next_page',
        (315, 26, 414, 113): 'e_up',
        (315, 212, 413, 302): 'e_down',
        (89, 28, 186, 111): 'baby_up',
        (88, 217, 187, 301): 'baby_down',
        (187, 129, 257, 193): 'baby2zoffset',
        }]


std_texts = [
        (14, 288, lambda ui: ui.printer.status_text),
    ]

# for each screen:
# text: x,y,text (handler function)
# rect: x,y,x2,y2,color (handler function)

std_icons = [
        (450, 5, lambda ui: 'icon_red' if ui.printer.offline else ('icon_blue' if ui.printer.paused else 'icon_green') ),
        (450, 40, lambda ui: 'icon_orange' if ui.event_queue else 'icon_grey' ),
    ]

widgets = [
    dict(texts=std_texts+[
        (157, 175, lambda ui: "BED: %.1f/%d"%ui.printer_info['bed']),
        (41 , 175, lambda ui: "E: %.1f/%d"%ui.printer_info['extruder']),
        (291, 175, lambda ui: "FAN: %.1f%%"%ui.printer.fan_speed.percentage),
        ], rects=[
            lambda ui: ((ui.size[0]-75, 12, 63, 100),
                (200 if ui.event_processed == -1 else 0, 255 if ui.event_processed == True else 0, 255 if ui.printer.printing else 0)),
            lambda ui: ((ui.size[0]-75, 108, 63, 200),
                (ui.event_queue, 255 if not ui.printer.offline else 0, 250 if ui.printer.paused else 0)),
            ]),
    dict(icons=std_icons,
        texts=std_texts+[
        (104, 5, lambda ui: "X%d"%ui.printer.position_x.value),
        (202, 5, lambda ui: "Y%d"%ui.printer.position_y.value),
        (343, 5, lambda ui: "Z%d"%ui.printer.position_z.value),
        ], rects=[]),
    dict(icons=std_icons,
        texts=std_texts+[
        (167 , 260, lambda ui: "%.1f/%d"%ui.printer_info['bed']),
        (34 , 260, lambda ui: "%.1f/%d"%ui.printer_info['extruder']),
        (321, 260, lambda ui: "%.1f%%"%ui.printer.fan_speed.percentage),
        ], rects=[]),
    dict(icons=std_icons,
        texts=std_texts+[
        (5 , 147, lambda ui: "%.2f"%ui.printer.baby_offset.value),
        (381 , 144, lambda ui: "%.2f"%ui.printer.position_e.value),
        (190, 205, lambda ui: "Z%.2f"% (-(ui.printer.position_z.value + ui.printer.baby_offset.value))),
        ], rects=[]),
    ]


text_color = (240, 250, 250)
