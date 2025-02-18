async function addTask() {
    const taskInput = document.getElementById('task');
    const timeInput = document.getElementById('time');
    const task = taskInput.value.trim();
    const time = timeInput.value;
    
    if (!task) {
        alert("Task cannot be empty");
        return;
    }
    
    try {
        const response = await fetch('https://daily-to-do-reminder-production.up.railway.app//add-task', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task, time})
        });
        
        if (!response.ok) {
            throw new Error('Failed to add task');
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
        const response = await fetch('https://daily-to-do-reminder-production.up.railway.app//list-tasks');
        
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
