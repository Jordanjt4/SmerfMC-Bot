document.querySelector(".dropdown").addEventListener('click', function() {
    this.focus();
    this.classList.toggle('active');

    const menu = this.querySelector('.dropdown-menu');
    menu.style.display = (menu.style.display === "none" || menu.style.display === "") ? "block" : "none"; // toggle display on or off
});

document.querySelectorAll('.dropdown-menu li').forEach(option => {
    option.addEventListener("click", function () {
        const dropdown = this.closest('.dropdown');
        const hiddenInput = dropdown.querySelector("input")
        const span = dropdown.querySelector('span');
        const form = dropdown.querySelector('form')

        span.textContent = this.textContent;
        console.log(this.textContent)
        hiddenInput.value = this.textContent;
        console.log(hiddenInput.value)
        form.submit()
    })
})