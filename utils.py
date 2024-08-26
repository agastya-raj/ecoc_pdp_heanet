FIRST_CENTRAL_FREQ = 191_350
CHANNEL_WIDTH = 50
CHANNEL_SPACING = 50
wdm_channel_list = list(range(1,96))

test1_patch_list = [
('tf_1', 'splitter_1_2x2_p1'),
('arof_sig', 'splitter_1_2x2_p2'),
('tf_2', 'roadm_4_p2'), 
('tf_3', 'roadm_4_p3'), 

('splitter_1_2x2_p1','roadm_4_p1'),

('roadm_4_line', 'fiber_temp_100m'), 
('fiber_temp_100m', 'roadm_3_line'), 

('roadm_3_p1', 'fiber_7_510m') ,
('fiber_7_510m', 'roadm_7_line'),

('roadm_7_p1', 'roadm_7_p1'),

('roadm_7_line', 'fiber_19_12646m'),
('fiber_19_12646m', 'roadm_8_line'),

('roadm_8_p1', 'roadm_8_p1'),

('roadm_8_line', 'fiber_18_25220m'),
('fiber_18_25220m', 'roadm_9_line'),

('roadm_9_p1', 'roadm_9_p1'),

('roadm_9_line', 'fiber_22_25332m'),
('fiber_22_25332m', 'roadm_6_line'),

('roadm_6_p1', 'roadm_6_p1'),

('roadm_6_line', 'fiber_17_665m'),
('fiber_17_665m', 'fiber_p1b_394m'),
('fiber_p1b_394m', 'roadm_5_line'),

('roadm_5_p1', 'roadm_5_p1'),

('roadm_5_line', 'fiber_15_11895m'),
('fiber_15_11895m', 'roadm_3_p1'),

('roadm_3_line', 'fiber_temp_268m'), 
('fiber_temp_268m', 'roadm_4_line'), 

('roadm_4_p1', 'tf_1'),
('roadm_4_p2', 'tf_2'), 
('roadm_4_p3', 'tf_3'), 

# ('roadm_4_p4', 'PH-AROF-1'), ## need to add 2 # disabling this for now
]

def nm_to_ghz(wavelength_nm):
    # Accurate speed of light in meters per second
    speed_of_light = 299_792_458  # m/s

    # Convert wavelength from nanometers to meters
    wavelength_m = wavelength_nm * 1e-9

    # Calculate frequency in Hz
    frequency_hz = speed_of_light / wavelength_m

    # Convert frequency to GHz
    frequency_ghz = frequency_hz * 1e-9

    return frequency_ghz

def get_freq_range(channel_num, channel_width=CHANNEL_WIDTH, channel_spacing=CHANNEL_SPACING, first_central_freq=FIRST_CENTRAL_FREQ):

    central_freq = first_central_freq + (channel_num-1)*channel_spacing
    start_freq = central_freq - channel_width/2.0
    end_freq = central_freq + channel_width/2.0

    return int(start_freq), int(central_freq), int(end_freq)

def generate_wide_channel_mux(roadm, channel_list, input_port, wss_id=1, output_port=4201,
                            loss=4.0,
                            open_channels=[],
                            channel_additional_attenuations=None,
                            blocked=False):
    # Makes one wide channel mux from multiple channles coming at input port

    if blocked == False:
        blocked_ = 'false'
    else:
        blocked_ = 'true'

    if isinstance(channel_list, int):
        channel_list = [channel_list]
    if isinstance(channel_list, tuple):
        channel_list = list(channel_list)
    if not isinstance(channel_list, list):
        raise ValueError("channel_list must be a tuple of integers, or an integer for single channels")
    
    start_freq = float(get_freq_range(channel_list[0])[0])
    end_freq = float(get_freq_range(channel_list[-1])[2])

    total_loss = float(loss) + (channel_additional_attenuations if channel_additional_attenuations is not None else 0.0)

    connection_id = str(channel_list[0])
    print(wss_id, connection_id, 'in-service', blocked_,input_port, output_port,str(start_freq),str(end_freq), '{:.2f}'.format(total_loss),  'CH' + connection_id)
    cur_conn = roadm.WSSConnection(
        wss_id, connection_id, 'in-service', blocked_,
        input_port, output_port,
        str(start_freq),
        str(end_freq),
        '{:.2f}'.format(total_loss),  'CH' + connection_id
    )
    return cur_conn

def operator_flex_grid_mux_connections(roadm, add_list, wss_id=1, output_port=4201,
                                channel_spacing=50.0, channel_width=50.0,central_freq_input=191350.0,
                                loss=4.0, channel_quantity=95,
                                open_channels=[],
                                channel_additional_attenuations=None,
                                default_port=1):
    
    # add_list is dict of form {channels, port}
    wss_connections_dwdm = []

    channel_port_dict = {}

    for channel in range(1,channel_quantity+1):
        for channel_list, port in add_list.items():
            if isinstance(channel_list, tuple):
                if channel in channel_list:
                    channel_port_dict[channel_list] = port
                    break
            elif isinstance(channel_list, int):
                if channel == channel_list:
                    channel_port_dict[channel_list] = port
                    break
        else:
            channel_port_dict[channel] = default_port

    for channel, port in channel_port_dict.items():

        input_port = 4100+port

        if isinstance(channel, tuple):
            if channel[0] in open_channels:
                blocked=False
            else:
                blocked=True
        elif isinstance(channel, int):
            if channel in open_channels:
                blocked=False
            else:
                blocked=True
        cur_conn = generate_wide_channel_mux(roadm, channel, input_port, loss=loss, open_channels=open_channels, channel_additional_attenuations=channel_additional_attenuations, blocked=blocked)
        wss_connections_dwdm.append(cur_conn)

    return wss_connections_dwdm

def generate_wide_channel_demux(roadm, channel_list, output_port, wss_id=2, input_port=5101,
                            loss=4.0,
                            open_channels=[],
                            channel_additional_attenuations=None,
                            blocked=False):
    # Makes one wide channel mux from multiple channles coming at input port

    if blocked == False:
        blocked_ = 'false'
    else:
        blocked_ = 'true'

    if isinstance(channel_list, int):
        channel_list = [channel_list]
    if isinstance(channel_list, tuple):
        channel_list = list(channel_list)
    if not isinstance(channel_list, list):
        raise ValueError("channel_list must be a tuple of integers, or an integer for single channels")

    start_freq = float(get_freq_range(channel_list[0])[0])
    end_freq = float(get_freq_range(channel_list[-1])[2])

    total_loss = float(loss) + (channel_additional_attenuations if channel_additional_attenuations is not None else 0.0)

    connection_id = str(channel_list[0])
    cur_conn = roadm.WSSConnection(
        wss_id, connection_id, 'in-service', blocked_,
        input_port, output_port,
        str(start_freq),
        str(end_freq),
        '{:.2f}'.format(total_loss),  'CH' + connection_id
    )
    return cur_conn

def operator_flex_grid_demux_connections(roadm, drop_list, wss_id=2, input_port=5101,
                                channel_spacing=50.0, channel_width=50.0,central_freq_input=191350.0,
                                loss=4.0, channel_quantity=95,
                                open_channels=[],
                                channel_additional_attenuations=None,
                                default_port=1):
    
    channel_port_dict = {}

    for channel in range(1,channel_quantity+1):
        for channel_list, port in drop_list.items():
            if isinstance(channel_list, tuple):
                if channel in channel_list:
                    channel_port_dict[channel_list] = port
                    break
            elif isinstance(channel_list, int):
                if channel == channel_list:
                    channel_port_dict[channel_list] = port
                    break
        else:
            channel_port_dict[channel] = default_port

    wss_connections_dwdm = []

    for channel, port in channel_port_dict.items():

        output_port = 5200+port

        if isinstance(channel, tuple):
            if channel[0] in open_channels:
                blocked=False
            else:
                blocked=True
        elif isinstance(channel, int):
            if channel in open_channels:
                blocked=False
            else:
                blocked=True
        # TODO: Can add channel-specific attenuations here later
        cur_conn = generate_wide_channel_demux(roadm, channel, output_port, loss=loss, open_channels=open_channels, channel_additional_attenuations=channel_additional_attenuations, blocked=blocked)
        wss_connections_dwdm.append(cur_conn)
    return wss_connections_dwdm

def operator_roadm_config(roadm, add_list, drop_list, open_channels=[],):

    ## MUX configuration
    conn_list = operator_flex_grid_mux_connections(roadm, add_list, open_channels=open_channels)
    roadm.wss_delete_connection(1, 'all')
    roadm.wss_add_connections(conn_list)

    ## DEMUX configuration
    conn_list = operator_flex_grid_demux_connections(roadm, drop_list, open_channels=open_channels)
    roadm.wss_delete_connection(2, 'all')
    roadm.wss_add_connections(conn_list)
