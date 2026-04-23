import speedtest

def run_speedtest():
    """Runs a speedtest and formats the output to match the requested UI."""
    st = speedtest.Speedtest()
    st.get_best_server()
    
    # Perform the tests
    st.download()
    st.upload(pre_allocate=False)
    
    # Fetch results dictionary and the share image URL
    results = st.results.dict()
    image_url = st.results.share()
    
    # Convert bits per second to Megabytes per second (MB/s)
    download_mbs = results['download'] / 1024 / 1024 / 8
    upload_mbs = results['upload'] / 1024 / 1024 / 8
    
    # Convert bytes to Megabytes
    data_sent_mb = results['bytes_sent'] / 1024 / 1024
    data_received_mb = results['bytes_received'] / 1024 / 1024
    
    server = results['server']
    
    # Construct the exact UI string
    caption = (
        f"⊃ *SPEEDTEST INFO*\n"
        f"├ *Upload:* {upload_mbs:.2f}MB/s\n"
        f"├ *Download:* {download_mbs:.2f}MB/s\n"
        f"├ *Ping:* {results['ping']} ms\n"
        f"├ *Time:*\n`{results['timestamp']}`\n"
        f"├ *Data Sent:* {data_sent_mb:.2f}MB\n"
        f"└ *Data Received:* {data_received_mb:.2f}MB\n\n"
        f"⊃ *SPEEDTEST SERVER*\n"
        f"├ *Name:* {server['name']}\n"
        f"├ *Country:* {server['country']}, {server['cc']}\n"
        f"├ *Sponsor:* {server['sponsor']}\n"
        f"├ *Latency:* {server['latency']}\n"
        f"├ *Latitude:* {server['lat']}\n"
        f"└ *Longitude:* {server['lon']}"
    )
    
    return image_url, caption
