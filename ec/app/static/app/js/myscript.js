$(document).ready(function(){

function getCookie(name) {
    var cookies = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return '';
}

function updateCart(url, id, success) {
    $.ajax({
        type: "POST",
        url: url,
        data: { prod_id: id },
        headers: { "X-CSRFToken": getCookie('csrftoken') },
        success: success,
        error: function() {
            window.alert("The cart could not be updated. Please refresh the page and try again.");
        }
    });
}

// ---------------- OWL ----------------
$('#slider1, #slider2, #slider3').owlCarousel({
    loop: true,
    margin: 20,
    responsiveClass: true,
    responsive: {
        0: { items: 2, nav: false, autoplay: true },
        600: { items: 4, nav: true, autoplay: true },
        1000: { items: 6, nav: true, loop: true, autoplay: true }
    }
});


// ---------------- PLUS CART ----------------
$(document).on('click', '.plus-cart', function(){
    var id = $(this).attr("pid").toString();
    var quantitySpan = $("#quantity-" + id);

    updateCart("/pluscart/", id, function(data){
            quantitySpan.text(data.quantity);
            $("#amount").text("Rs. " + data.amount);
            $("#totalamount").text("Rs. " + data.totalamount);
    });
});


// ---------------- MINUS CART ----------------
$(document).on('click', '.minus-cart', function(){
    var id = $(this).attr("pid").toString();
    var quantitySpan = $("#quantity-" + id);

    updateCart("/minuscart/", id, function(data){
            quantitySpan.text(data.quantity);
            $("#amount").text("Rs. " + data.amount);
            $("#totalamount").text("Rs. " + data.totalamount);
    });
});


// ---------------- REMOVE CART ----------------
$(document).on('click', '.remove-cart', function(e){
    e.preventDefault();

    var id = $(this).attr("pid").toString();
    var row = $(this).closest('.cart-item');

    updateCart("/removecart/", id, function(data){

            $("#amount").text("Rs. " + data.amount);
            $("#totalamount").text("Rs. " + data.totalamount);

            row.fadeOut(300, function(){
                $(this).remove();

                // if empty reload
                if ($('.cart-item').length === 0){
                    location.reload();
                }
            });
    });
});

});