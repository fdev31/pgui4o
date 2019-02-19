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
        (405, 13, 465, 107): 'ui_main_page',
        (405, 111, 468, 307): 'ui_next_page',
        (201, 27, 281, 110): 'home',
        (88, 164, 148, 219): 'home_xy',
        (287, 162, 323, 204): 'home_z',
        (99, 92, 138, 149): 'y_up',
        (102, 231, 143, 291): 'y_down',
        (17, 171, 82, 212): 'x_down',
        (159, 169, 222, 213): 'x_up',
        (301, 86, 340, 149): 'z_up',
        (302, 230, 342, 293): 'z_down',
        (360, 113, 391, 159): 'z_up_small',
        (357, 220, 396, 271): 'z_down_small',
        },
    {
        (405, 13, 465, 107): 'ui_main_page',
        (405, 111, 468, 307): 'ui_next_page',
        (60, 82, 119, 147): 'e_temp_up',
        (66, 152, 117, 215): 'e_temp_down',
        (196, 82, 251, 146): 'bed_temp_up',
        (195, 155, 252, 216): 'bed_temp_down',
        (334, 85, 395, 153): 'fan_up',
        (334, 158, 390, 225): 'fan_down',
        },
    {
        (405, 13, 465, 107): 'ui_main_page',
        (405, 111, 468, 307): 'ui_next_page',
        (102, 70, 177, 163): 'e_up',
        (100, 172, 176, 272): 'e_down',
        (301, 73, 363, 162): 'baby_up',
        (301, 173, 366, 267): 'baby_down',
        (191, 265, 281, 298): 'baby2zoffset',
        }]


std_rects = [
    lambda ui: ((ui.size[0]-75, 12, 63, 100),
        (200 if ui.event_processed == -1 else 0, 255 if ui.event_processed == True else 0, 255 if ui.printer.printing else 0)),
    lambda ui: ((ui.size[0]-75, 108, 63, 200),
        (ui.event_queue, 255 if not ui.printer.offline else 0, 250 if ui.printer.paused else 0)),
    ]

std_texts = [
        (14, 288, lambda ui: ui.printer.status_text),
    ]
# for each screen:
# text: x,y,text (handler function)
# rect: x,y,x2,y2,color (handler function)

widgets = [
    dict(texts=std_texts+[
        (157, 175, lambda ui: "BED: %.1f/%d"%ui.printer_info['bed']),
        (41 , 175, lambda ui: "E: %.1f/%d"%ui.printer_info['extruder']),
        (291, 175, lambda ui: "FAN: %.1f%%"%ui.printer.fan_speed.percentage),
        ], rects=std_rects),
    dict(texts=std_texts+[
        (18 , 63, lambda ui: "X%d"%ui.printer.position_x.value),
        (70 , 63, lambda ui: "Y%d"%ui.printer.position_y.value),
        (120, 63, lambda ui: "Z%d"%ui.printer.position_z.value),
        ], rects=std_rects),
    dict(texts=std_texts+[
        (137, 65, lambda ui: "%.1f/%d"%ui.printer_info['bed']),
        (21 , 65, lambda ui: "%.1f/%d"%ui.printer_info['extruder']),
        (271, 65, lambda ui: "%.1f%%"%ui.printer.fan_speed.percentage),
        ], rects=std_rects),
    dict(texts=std_texts+[
        (241, 110, lambda ui: "%.2f"%ui.printer.baby_offset.value),
        (289 , 273, lambda ui: "Z%.2f"% (-(ui.printer.position_z.value + ui.printer.baby_offset.value))),
        ], rects=std_rects),
    ]

text_color = (0, 0, 0)
