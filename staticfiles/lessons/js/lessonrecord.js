document.addEventListener("DOMContentLoaded", function () {
    console.log("LessonRecord JS loaded ✅");

    const teacherField = document.querySelector("#id_created_by");
    const timetableField = document.querySelector("#id_timetable");

    console.log("teacherField:", teacherField);
    console.log("timetableField:", timetableField);

    if (teacherField && timetableField) {
        teacherField.addEventListener("change", function () {
            console.log("Teacher changed to:", this.value);

            const teacherId = this.value;
            if (!teacherId) {
                timetableField.innerHTML = '<option value="">---------</option>';
                return;
            }

            fetch(`/lessons/ajax/load-timetables/?teacher=${teacherId}`)
                .then(response => response.json())
                .then(data => {
                    console.log("Received timetables:", data);
                    timetableField.innerHTML = '<option value="">---------</option>';
                    data.forEach(function (item) {
                        const option = document.createElement("option");
                        option.value = item.id;
                        option.textContent = `${item.subject} (${item.day} ${item.start_time}-${item.end_time})`;
                        timetableField.appendChild(option);
                    });
                })
                .catch(error => console.error("Error loading timetables:", error));
        });
    } else {
        console.warn("Could not find teacher or timetable field ❌");
    }
});