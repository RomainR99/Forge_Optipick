def assignment_to_allocation(assign_array, order_ids, agent_ids):
    allocation = {aid: [] for aid in agent_ids}
    for i, agent_index in enumerate(assign_array):
        oid = order_ids[i]
        aid = agent_ids[int(agent_index) - 1]  # 1-based -> 0-based
        allocation[aid].append(oid)
    return allocation
