"Build a Databricks App using app and Lakebase (PostgreSQL Autoscaling) as the backend to simulate a Veeva Vault Batch Release dashboard for the drug Stelara.
The App requirements:
	1	Data Layer: Use Lakebase to store a table called batch_disposition with columns: batch_id, status (Pending, Released, Rejected), temp_check (Boolean), purity_check (Boolean), and last_updated.
	2	Header: A high-level 'Executive KPI' strip showing 'Batches Pending Release' and 'Average Cycle Time.'
	3	Main View: A searchable table of Stelara batches. Use visual 'Traffic Light' indicators (Green/Red) to show if the Batch stayed within $37^\circ\text{C} \pm 0.5^\circ\text{C}$ and if purity is $>98\%$.
	4	Interaction: When a user clicks a 'Pending' batch, open a side panel (simulating Veeva) that shows the 'Exceptions.' Include a 'Digital Sign-Off' button that updates the Lakebase record to 'Released' via a SQL UPDATE query.
	5	Visual Style: Keep it clean and 'Enterprise'—use a white/blue color palette similar to Veeva's UI. Use the 'Review by Exception' philosophy where only failing parameters are highlighted in red."

See attached screenshots for reference on the UI design
Deploy to databricks using HLS environment
