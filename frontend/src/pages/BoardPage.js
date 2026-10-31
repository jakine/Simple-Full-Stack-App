import TaskBoard from "../components/TaskBoard";
import { PageHeader } from "../components/ui";

function BoardPage() {
  return (
    <div>
      <PageHeader title="Board">
        Drag a task into another column to change its status. Open a card to edit details, comment, or see history.
      </PageHeader>
      <TaskBoard />
    </div>
  );
}

export default BoardPage;
