document.addEventListener("DOMContentLoaded", function () {
    const teacherField = document.querySelector("#id_created_by");
    const weekField = document.querySelector("#id_week");
    const timetableField = document.querySelector("#id_timetable");

    function loadTimetables() {
        const teacherId = teacherField.value;
        const weekId = weekField.value;

        if (!teacherId) {
            timetableField.innerHTML = '<option value="">---------</option>';
            return;
        }

        // ✅ Correct fetch syntax with /lessons/ prefix
        fetch(`/lessons/ajax/load-timetables/?teacher=${teacherId}&week=${weekId}`)
            .then(response => response.json())
            .then(data => {
                timetableField.innerHTML = '<option value="">---------</option>';
                data.forEach(item => {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.textContent = item.name;
                    timetableField.appendChild(option);
                });
            })
            .catch(error => console.error("Error loading timetables:", error));
    }

    teacherField.addEventListener("change", loadTimetables);
    weekField.addEventListener("change", loadTimetables);
});
