import json
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import math

sz = "1mb"

def do_plot():
    print(sz)

    with open(f'overheads/write_minio_{sz}.json') as data:
        minio_write = json.loads(data.read())

    with open(f'overheads/write_s3proxy_{sz}.json') as data:
        proxy_write = json.loads(data.read())

    with open(f'overheads/write_active_{sz}.json') as data:
        active_write = json.loads(data.read())
    
    minio_write_data = sorted([x['elpased'] / 1000000 for x in minio_write], reverse=True)[15:-15]
    proxy_write_data = sorted([x['elpased'] / 1000000 for x in proxy_write], reverse=True)[15:-15]
    active_write_data = sorted([x['elpased'] / 1000000 for x in active_write], reverse=True)[15:-15]

    print('--- write ---')
    print('MinIO mean', np.mean(minio_write_data), 'ms')
    print('MinIO median', np.median(minio_write_data), 'ms')
    print('MinIO min', np.min(minio_write_data), 'ms')
    print('MinIO max', np.max(minio_write_data), 'ms')
    print('s3proxy mean', np.mean(proxy_write_data), 'ms')
    print('s3proxy median', np.median(proxy_write_data), 'ms')
    print('s3proxy min', np.min(proxy_write_data), 'ms')
    print('s3proxy max', np.max(proxy_write_data), 'ms')
    print('Active s3proxy mean', np.mean(active_write_data), 'ms')
    print('Active s3proxy median', np.median(active_write_data), 'ms')
    print('Active s3proxy min', np.min(active_write_data), 'ms')
    print('Active s3proxy max', np.max(active_write_data), 'ms')

    with open(f'overheads/read_minio_{sz}.json') as data:
        minio_read = json.loads(data.read())

    with open(f'overheads/read_s3proxy_{sz}.json') as data:
        proxy_read = json.loads(data.read())

    with open(f'overheads/read_active_{sz}.json') as data:
        active_read = json.loads(data.read())
    
    minio_read_data = sorted([x['elpased'] / 1000000 for x in minio_read], reverse=True)[15:-15]
    proxy_read_data = sorted([x['elpased'] / 1000000 for x in proxy_read], reverse=True)[15:-15]
    active_read_data = sorted([x['elpased'] / 1000000 for x in active_read], reverse=True)[15:-15]

    print('--- read ---')
    print('MinIO mean', np.mean(minio_read_data), 'ms')
    print('MinIO median', np.median(minio_read_data), 'ms')
    print('MinIO min', np.min(minio_read_data), 'ms')
    print('MinIO max', np.max(minio_read_data), 'ms')
    print('s3proxy mean', np.mean(proxy_read_data), 'ms')
    print('s3proxy median', np.median(proxy_read_data), 'ms')
    print('s3proxy min', np.min(proxy_read_data), 'ms')
    print('s3proxy max', np.max(proxy_read_data), 'ms')
    print('Active s3proxy mean', np.mean(active_read_data), 'ms')
    print('Active s3proxy median', np.median(active_read_data), 'ms')
    print('Active s3proxy min', np.min(active_read_data), 'ms')
    print('Active s3proxy max', np.max(active_read_data), 'ms')

    fig, (ax1, ax2) = plt.subplots(1, 2)

    bp1 = ax1.boxplot([minio_write_data, proxy_write_data, active_write_data], labels=['MinIO', 's3proxy', 'Active\ns3proxy'], patch_artist=True)
    ax1.set_ylabel("PUT total time (ms)")
    bp2 = ax2.boxplot([minio_read_data, proxy_read_data, active_read_data], labels=['MinIO', 's3proxy', 'Active\ns3proxy'], patch_artist=True)
    ax2.set_ylabel("GET total time (ms)")

    colors = ['pink', 'lightblue', 'lightgreen']
    for bplot in (bp1, bp2):
        for patch, color in zip(bplot['boxes'], colors):
            patch.set_facecolor(color)

    fig.set_size_inches(10, 8)
    fig.suptitle('No-op PUT/GET 100 MiB payload')
    fig.tight_layout()
    # plt.show()
    fig.savefig(f'overhead_{sz}.png')




if __name__ == '__main__':
    sns.set_theme()
    do_plot()

# ax = sns.boxplot(x="x", y="elapsed", data=)
