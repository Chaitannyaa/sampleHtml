import psycopg2
import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="postgresdb",
    user="postgres",
    password="mysecretpassword",
    port="5432"
)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS poll_results (
        id SERIAL PRIMARY KEY,
        tool VARCHAR(255) NOT NULL,
        count INT NOT NULL
    )
""")
conn.commit()
# Retrieve the poll results from Redis
poll_results = r.hgetall('poll_results')

# Calculate the total count for each orchestration tool
counts = {
    'Kubernetes': 0,
    'Docker Swarm': 0,
    'Mesos': 0,
    'Nomad': 0
}
for key, value in poll_results.items():
    counts[key.decode('utf-8')] = int(value)

# Determine the most popular orchestration tool
max_count = max(counts.values())
popular_tools = [k for k, v in counts.items() if v == max_count]

# Store the poll results in PostgreSQL
for tool, count in counts.items():
    cur.execute("SELECT count FROM poll_results WHERE tool = %s", (tool,))
    row = cur.fetchone()
    if row:
        # Increment the count if the row already exists
        cur.execute("UPDATE poll_results SET count = %s WHERE tool = %s", (count, tool))
    else:
        # Insert a new row if the row does not exist
        cur.execute("INSERT INTO poll_results (tool, count) VALUES (%s, %s)", (tool, count))
conn.commit()


# Close database connection
cur.close()
conn.close()

# Print the poll results and the most popular orchestration tool(s)
print(poll_results)
print('Poll Results:')
print('--------------')
print(f'Kubernetes: {counts["Kubernetes"]}')
print(f'Docker Swarm: {counts["Docker Swarm"]}')
print(f'Mesos: {counts["Mesos"]}')
print(f'Nomad: {counts["Nomad"]}')
print('')
if len(popular_tools) == 1:
    print(f'{popular_tools[0]} is the most popular orchestration tool with {max_count} votes.')
else:
    print('The following orchestration tools are tied for most popular:')
    for tool in popular_tools:
        print(f'{tool}: {max_count} votes')
