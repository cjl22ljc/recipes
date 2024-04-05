from orch.api_functions import *
from prefect import task, flow
import asyncio

# we got these api functions. Now define a complete procedure to do a 100x serial dilution
# x100 serial dilution of reagent idx=4 in idx=0.

# process to dispense an item from the inventory and moving it to an incub.


@task
async def dispense_one_tube(reagent_idx, volume, temperature):
    ## represents a sequential unit of operations involving INV0
    # acquire inventory
    key_inv = await acquire_dev("INV0")
    # allocate one slot
    storage_inv = await allocate_slots(1, "solo_15", "INV0")
    # create a tube in the slot
    await create_tube(storage_inv, 0)
    # dispense
    await dispense_reagent(storage_inv, 0, reagent_idx, volume, temperature)
    ## move the tube to a slot in INC0
    # acquire INC0
    key_inc = await acquire_dev("INC0")
    # allocate one slot
    storage_inc = await allocate_slots(1, "solo_15", "INC0")
    # move from inv to inc
    await move(storage_inv, 0, storage_inc, 0)
    # release storage_inv
    await release_slots(storage_inv)
    # release inv
    await release_dev(key_inv)
    ## now we've got the tube in INC0
    await release_dev(key_inv)

    return storage_inc


@flow(name="serial_dilution", log_prints=True)
async def serial_dilution():
    storage = await dispense_one_tube(4, 10.0, 5.0)
    tube = await lookup(storage, 0)
    print(tube)


@task
def test():
    print("test")


@flow
def my_flow():
    asyncio.run(serial_dilution())


if __name__ == "__main__":
    my_flow.deploy(
        name="serial_dilution_deployment",
        work_pool_name="test-pool",
        work_queue_name="default",
    )
