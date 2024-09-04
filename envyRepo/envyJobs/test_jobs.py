import envyRepo.prep_env
import job
from enums import Purpose as p
from datetime import datetime

test_job = job.Job(f"potato - {datetime.now().strftime('%d-%m-%Y %H-%M-%S')}")
test_job.add_range(1, 150, 1)
test_job.set_meta()
test_job.set_allocation(10)
test_job.set_purpose(p.CACHE)
test_job.set_type('PLUGIN_EXAMPLE')
test_job.set_environment({
})
test_job.set_parameters({
    'A': 5
})
test_job.write()