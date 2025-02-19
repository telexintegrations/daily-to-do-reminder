
async function addTask() {
    const taskInput = document.getElementById('task');
    const timeInput = document.getElementById('time');
    const dateInput = document.getElementById('date');
    const task = taskInput.value.trim();
    const time = timeInput.value;
    const date = dateInput.value;
    
    if (!task) {
        alert("Task cannot be empty");
        return;
    }
    if (date < new Date().toISOString().split('T')[0]) {
        alert("Date cannot be in the past");
        return;
    }
    if (date === new Date().toISOString().split('T')[0] && time < new Date().toTimeString().split(' ')[0].substring(0, 5)) {
        alert("Time cannot be in the past");
        return;
    }
    
    try {
        const response = await fetch('https://daily-to-do-reminder.onrender.com/add-task', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task, time, date})
        });
        
        if (!response.ok) {
            throw new Error('Failed to add task, present date or time');
        }
        
        const result = await response.json();
        alert(result.message);
        taskInput.value = '';
        loadTasks();
    } catch (error) {
        alert("Error: " + error.message);
    }
}


async function loadTasks() {
    try {
        const response = await fetch('https://daily-to-do-reminder.onrender.com/list-tasks');
        
        if (!response.ok) {
            throw new Error('Failed to fetch tasks');
        }
        
        const data = await response.json();
        const taskList = document.getElementById('taskList');
        taskList.innerHTML = '';
        
        data.tasks.forEach(task => {
            const li = document.createElement('li');
            li.textContent = task;
            taskList.appendChild(li);
        });
    } catch (error) {
        alert("Error loading tasks: " + error.message);
    }
}

loadTasks();
