import { Link } from "react-router-dom";
import TaskTimeline from "../components/TaskTimeline";
import { PageHeader } from "../components/ui";

function TimelinePage() {
  return (
    <div>
      <PageHeader title="Timeline">
        Tasks with a start or due date appear as bars. Group by phase or team, and switch between weeks and months. Add
        or rename phases in <Link to="/settings/workflow">Workflow</Link>.
      </PageHeader>
      <TaskTimeline />
    </div>
  );
}

export default TimelinePage;
