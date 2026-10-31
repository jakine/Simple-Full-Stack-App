import WorkSheet from "../components/WorkSheet";
import { PageHeader } from "../components/ui";

function SheetPage() {
  return (
    <div>
      <PageHeader title="Sheet">
        Pick a day, a week, or a month on the calendar, then fill the amount for each day. Quantity columns write the
        same reports as the rest of the project.
      </PageHeader>
      <WorkSheet />
    </div>
  );
}

export default SheetPage;
